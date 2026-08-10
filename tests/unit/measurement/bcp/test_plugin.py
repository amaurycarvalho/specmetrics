from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from structlog.testing import capture_logs

from specmetrics.kernel.cfm.model import (
    BuildMetadata,
    CanonicalFunctionalModel,
    EvidenceRef,
    FunctionalProcess,
)
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.plugins.measurement.bcp import plugin as bcp_plugin_module
from specmetrics.plugins.measurement.bcp.models import (
    BCPMeasurementResult,
    BCPWorkItem,
    ExecutionMetadata,
    MeasurementWarning,
)
from specmetrics.plugins.measurement.bcp.plugin import (
    BCPHandler,
    BCPPlugin,
    create_bcp_measurement_metadata,
)


def _make_cfm() -> CanonicalFunctionalModel:
    ev = EvidenceRef(graph_node_id="gn-1", document_id="doc-1", text="ev")
    fps = {}
    for i in range(2):
        fid = f"fp-{i}"
        fps[fid] = FunctionalProcess(id=fid, name=f"Process {i}", evidence=ev)
    return CanonicalFunctionalModel(
        run_id="cfm-test",
        functional_processes=fps,
        metadata=BuildMetadata(run_id="cfm-test"),
    )


def _make_success_item() -> BCPWorkItem:
    return BCPWorkItem(
        element_id="fp-0",
        element_name="Process 0",
        generated_story="story",
        bcp_score=10.0,
        component_breakdown={"complexity": 10.0},
        status="success",
    )


def _make_failed_item() -> BCPWorkItem:
    return BCPWorkItem(
        element_id="fp-1",
        element_name="Process 1",
        generated_story="story",
        bcp_score=0.0,
        component_breakdown={},
        status="failed",
    )


def _make_result() -> BCPMeasurementResult:
    return BCPMeasurementResult(
        run_id="run-1",
        sdk_version="1.2.3",
        provider="openai",
        items=[_make_success_item(), _make_failed_item()],
        total_bcp=10.0,
        execution_metadata=ExecutionMetadata(
            duration_ms=12.34,
            total_fps_processed=2,
            items_succeeded=1,
            items_failed=1,
            sdk_call_count=2,
            sdk_errors=0,
        ),
        warnings=[
            MeasurementWarning(code="W1", message="Warning one"),
        ],
    )


@pytest.fixture
def cfm() -> CanonicalFunctionalModel:
    return _make_cfm()


class TestCreateBcpMeasurementMetadata:
    def test_metadata_values(self) -> None:
        md = create_bcp_measurement_metadata()
        assert md.id == "bcp"
        assert md.api_version == "0.1.0"
        assert md.plugin_type.value == "measurement"
        assert md.handled_event_types == (EventType.MEASUREMENT_COMPLETED,)
        assert md.name == "BCP"
        assert md.description == (
            "Business Complexity Points — estimates business complexity "
            "via external LLM-based SDK from CFM"
        )
        assert md.version == "0.1.0"
        handler = md.handler_factory()
        assert isinstance(handler, BCPHandler)


class TestBCPHandlerProperties:
    def test_properties(self) -> None:
        handler = BCPHandler()
        assert handler.handled_event_type == EventType.MEASUREMENT_COMPLETED
        assert handler.handler_id == "bcp_measurement"
        assert handler.stage_name == "BCP Measurement"


class TestBCPHandlerHandle:
    def test_handle_no_cfm_logs(self) -> None:
        ctx = PipelineContext()
        event = PipelineEvent(
            event_type=EventType.MEASUREMENT_COMPLETED,
            publisher="test",
            payload={},
            context=ctx,
        )
        handler = BCPHandler()
        with capture_logs() as captured:
            result = handler.handle(event)
        assert "bcp_measurement_started" in {e["event"] for e in captured}
        started = next(
            e for e in captured if e["event"] == "bcp_measurement_started"
        )
        assert started["execution_id"] == str(ctx.execution_id)
        assert started["has_cfm"] is False
        assert result.measurement_result is not None
        assert result.measurement_result["bcp_total_bcp"] == 0.0
        assert result.measurement_result["bcp_items_failed"] == 0

    def test_handle_with_cfm_logs_and_payload(
        self, cfm: CanonicalFunctionalModel, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ctx = PipelineContext()
        ctx = ctx.with_stage_output("canonical_model", cfm)
        event = PipelineEvent(
            event_type=EventType.MEASUREMENT_COMPLETED,
            publisher="test",
            payload={},
            context=ctx,
        )
        handler = BCPHandler()
        received: dict[str, object] = {}
        def fake_measure(cfm, run_id):
            received["run_id"] = run_id
            received["cfm"] = cfm
            return _make_result()
        monkeypatch.setattr(handler, "_measure", fake_measure)
        with capture_logs() as captured:
            result = handler.handle(event)
        events = {e["event"] for e in captured}
        assert "bcp_measurement_started" in events
        assert "bcp_measurement_completed" in events
        assert received["run_id"] == str(ctx.execution_id)
        assert received["cfm"] is cfm
        started = next(
            e for e in captured if e["event"] == "bcp_measurement_started"
        )
        assert started["has_cfm"] is True
        completed = next(
            e for e in captured if e["event"] == "bcp_measurement_completed"
        )
        assert completed["total_bcp"] == 10.0
        assert completed["measured_items"] == 2
        assert completed["duration_ms"] == 12.34
        payload = result.measurement_result
        assert payload["bcp_method"] == "BCP"
        assert payload["bcp_sdk_version"] == "1.2.3"
        assert payload["bcp_provider"] == "openai"
        assert payload["bcp_total_bcp"] == 10.0
        assert payload["bcp_measured_items"] == 2
        assert payload["bcp_items_succeeded"] == 1
        assert payload["bcp_items_failed"] == 1
        assert payload["bcp_duration_ms"] == 12.34
        assert payload["bcp_warnings"] == [
            {"code": "W1", "message": "Warning one", "element_id": None}
        ]
        entities = payload["bcp_entities"]
        assert len(entities) == 1
        assert entities[0] == {
            "element_id": "fp-0",
            "element_name": "Process 0",
            "bcp_score": 10.0,
            "component_breakdown": {"complexity": 10.0},
            "generated_story": "story",
            "status": "success",
        }
        assert len(result.published_events) == 1
        published = result.published_events[0]
        assert published.event_type == EventType.MEASUREMENT_COMPLETED
        assert published.publisher == "bcp"
        assert published.payload == payload
        assert published.context is ctx


class TestBCPHandlerMeasure:
    def test_measure_missing_cfm(self) -> None:
        handler = BCPHandler()
        result = handler._measure(None, "run-1")
        assert result.run_id == "run-1"
        assert result.total_bcp == 0.0
        assert result.items == []
        assert result.execution_metadata.duration_ms == 0.0
        assert result.execution_metadata.total_fps_processed == 0
        assert len(result.warnings) == 1
        assert result.warnings[0].code == "MISSING_CFM"
        assert result.warnings[0].message == (
            "Canonical Functional Model is not available. "
            "BCP measurement skipped."
        )

    def test_measure_sdk_not_available(
        self, cfm: CanonicalFunctionalModel, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        adapter = MagicMock()
        adapter.is_available = False
        adapter._import_error = "boom"
        monkeypatch.setattr(bcp_plugin_module, "BcpSdkAdapter", lambda provider: adapter)
        monkeypatch.setenv("BCP_PROVIDER", "anthropic")
        handler = BCPHandler()
        result = handler._measure(cfm, "run-1")
        assert result.run_id == "run-1"
        assert result.provider == "anthropic"
        assert result.total_bcp == 0.0
        assert result.items == []
        assert result.execution_metadata.duration_ms == 0.0
        assert result.execution_metadata.total_fps_processed == 0
        assert result.warnings[0].code == "SDK_NOT_AVAILABLE"
        assert result.warnings[0].message == "boom"

    def test_measure_sdk_not_available_fallback_message(
        self, cfm: CanonicalFunctionalModel, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        adapter = MagicMock()
        adapter.is_available = False
        adapter._import_error = None
        monkeypatch.setattr(bcp_plugin_module, "BcpSdkAdapter", lambda provider: adapter)
        handler = BCPHandler()
        result = handler._measure(cfm, "run-1")
        assert result.warnings[0].code == "SDK_NOT_AVAILABLE"
        assert result.warnings[0].message == (
            "BCP SDK not available. Install with: pip install bcp-calculator"
        )

    def test_measure_provider_passed_to_adapter(
        self, cfm: CanonicalFunctionalModel, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        adapter = MagicMock()
        adapter.is_available = True
        adapter._import_error = None
        created: list[str] = []
        def factory(provider):
            created.append(provider)
            return adapter
        monkeypatch.setattr(bcp_plugin_module, "BcpSdkAdapter", factory)
        monkeypatch.setattr(bcp_plugin_module, "check_credentials", lambda provider: None)
        monkeypatch.setattr(
            bcp_plugin_module,
            "measure_all",
            lambda *args, **kwargs: ([_make_success_item(), _make_failed_item()], 1, 1, 2, 0),
        )
        handler = BCPHandler()
        handler._measure(cfm, "run-1")
        assert created == ["openai"]

    def test_measure_check_credentials_receives_provider(
        self, cfm: CanonicalFunctionalModel, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        adapter = MagicMock()
        adapter.is_available = True
        adapter._import_error = None
        monkeypatch.setattr(bcp_plugin_module, "BcpSdkAdapter", lambda provider: adapter)
        called: list[str] = []
        def creds(provider):
            called.append(provider)
        monkeypatch.setattr(bcp_plugin_module, "check_credentials", creds)
        monkeypatch.setattr(
            bcp_plugin_module,
            "measure_all",
            lambda *args, **kwargs: ([_make_success_item(), _make_failed_item()], 1, 1, 2, 0),
        )
        handler = BCPHandler()
        handler._measure(cfm, "run-1")
        assert called == ["openai"]

    def test_measure_missing_credentials(
        self, cfm: CanonicalFunctionalModel, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        adapter = MagicMock()
        adapter.is_available = True
        adapter._import_error = None
        monkeypatch.setattr(bcp_plugin_module, "BcpSdkAdapter", lambda provider: adapter)
        monkeypatch.setattr(bcp_plugin_module, "check_credentials", lambda provider: "OPENAI_API_KEY")
        monkeypatch.setenv("BCP_PROVIDER", "anthropic")
        handler = BCPHandler()
        result = handler._measure(cfm, "run-1")
        assert result.run_id == "run-1"
        assert result.provider == "anthropic"
        assert result.total_bcp == 0.0
        assert result.items == []
        assert result.execution_metadata.duration_ms == 0.0
        assert result.execution_metadata.total_fps_processed == 0
        assert result.warnings[0].code == "MISSING_CREDENTIALS"
        assert result.warnings[0].message == (
            "Missing OPENAI_API_KEY environment variable. "
            "Set it in .env or environment."
        )

    def test_measure_success(
        self, cfm: CanonicalFunctionalModel, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        adapter = MagicMock()
        adapter.is_available = True
        adapter._import_error = None
        monkeypatch.setattr(bcp_plugin_module, "BcpSdkAdapter", lambda provider: adapter)
        monkeypatch.setattr(bcp_plugin_module, "check_credentials", lambda provider: None)
        monkeypatch.setenv("BCP_PROVIDER", "anthropic")
        monkeypatch.setattr(
            bcp_plugin_module,
            "measure_all",
            lambda *args, **kwargs: ([_make_success_item(), _make_failed_item()], 1, 1, 2, 3),
        )
        handler = BCPHandler()
        result = handler._measure(cfm, "run-1")
        assert result.run_id == "run-1"
        assert result.provider == "anthropic"
        assert result.total_bcp == 10.0
        assert len(result.items) == 2
        assert result.execution_metadata.total_fps_processed == 2
        assert result.execution_metadata.items_succeeded == 1
        assert result.execution_metadata.items_failed == 1
        assert result.execution_metadata.sdk_call_count == 2
        assert result.execution_metadata.sdk_errors == 3
        assert result.warnings == []
        assert result.execution_metadata.duration_ms >= 0.0
        assert result.execution_metadata.duration_ms == round(
            result.execution_metadata.duration_ms, 2
        )

    def test_measure_duration_uses_elapsed_ms(
        self, cfm: CanonicalFunctionalModel, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import time as _time

        adapter = MagicMock()
        adapter.is_available = True
        adapter._import_error = None
        monkeypatch.setattr(bcp_plugin_module, "BcpSdkAdapter", lambda provider: adapter)
        monkeypatch.setattr(bcp_plugin_module, "check_credentials", lambda provider: None)
        monkeypatch.setattr(
            bcp_plugin_module,
            "measure_all",
            lambda *args, **kwargs: ([_make_success_item(), _make_failed_item()], 1, 1, 2, 0),
        )
        counter = [0.0]

        def fake_monotonic():
            counter[0] += 1.0
            return counter[0]

        monkeypatch.setattr(_time, "monotonic", fake_monotonic)
        counter = [0.0]

        def fake_monotonic():
            counter[0] += 0.567897
            return counter[0]

        monkeypatch.setattr(_time, "monotonic", fake_monotonic)
        handler = BCPHandler()
        result = handler._measure(cfm, "run-1")
        assert result.execution_metadata.duration_ms == round(567.897, 2)

    def test_handler_measure_duration_uses_elapsed_ms(
        self, cfm: CanonicalFunctionalModel, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import time as _time

        adapter = MagicMock()
        adapter.is_available = True
        adapter._import_error = None
        monkeypatch.setattr(bcp_plugin_module, "BcpSdkAdapter", lambda provider: adapter)
        monkeypatch.setattr(
            bcp_plugin_module,
            "measure_all",
            lambda cfm, adapter, **kw: ([_make_success_item(), _make_failed_item()], 1, 1, 2, 0),
        )
        counter = [0.0]

        def fake_monotonic():
            counter[0] += 0.567897
            return counter[0]

        monkeypatch.setattr(_time, "monotonic", fake_monotonic)
        result = BCPPlugin._handler_measure(cfm)
        assert result.execution_metadata.duration_ms == round(567.897, 2)

    def test_resolve_provider_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("BCP_PROVIDER", raising=False)
        handler = BCPHandler()
        assert handler._resolve_provider() == "openai"

    def test_measure_success_sets_gauge(
        self, cfm: CanonicalFunctionalModel, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        adapter = MagicMock()
        adapter.is_available = True
        adapter._import_error = None
        monkeypatch.setattr(bcp_plugin_module, "BcpSdkAdapter", lambda provider: adapter)
        monkeypatch.setattr(bcp_plugin_module, "check_credentials", lambda provider: None)
        monkeypatch.setattr(
            bcp_plugin_module,
            "measure_all",
            lambda *args, **kwargs: ([_make_success_item(), _make_failed_item()], 1, 1, 2, 0),
        )
        gauge = MagicMock()
        monkeypatch.setattr(bcp_plugin_module, "_story_gauge", gauge)
        handler = BCPHandler()
        result = handler._measure(cfm, "run-1")
        gauge.set.assert_called_once_with(2)
        assert result.total_bcp == 10.0

    def test_resolve_provider_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("BCP_PROVIDER", "anthropic")
        handler = BCPHandler()
        assert handler._resolve_provider() == "anthropic"

    def test_measure_fps_uses_measure_all(
        self, cfm: CanonicalFunctionalModel, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: dict[str, object] = {}
        monkeypatch.setattr(
            bcp_plugin_module,
            "measure_all",
            lambda cfm, adapter, **kw: calls.update(kw) or (
                [_make_success_item()],
                1,
                0,
                1,
                0,
            ),
        )
        handler = BCPHandler()
        result = handler._measure_fps(cfm, MagicMock())
        assert calls["include_evidence"] is True
        assert callable(calls["record_request"])
        assert callable(calls["record_success"])
        assert callable(calls["record_error"])
        assert result == ([_make_success_item()], 1, 0, 1, 0)

    def test_measure_fps_callbacks_use_telemetry(
        self, cfm: CanonicalFunctionalModel, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        requests = MagicMock()
        duration = MagicMock()
        errors = MagicMock()
        monkeypatch.setattr(bcp_plugin_module, "_sdk_requests", requests)
        monkeypatch.setattr(bcp_plugin_module, "_sdk_duration", duration)
        monkeypatch.setattr(bcp_plugin_module, "_sdk_errors", errors)
        captured: dict[str, object] = {}
        monkeypatch.setattr(
            bcp_plugin_module,
            "measure_all",
            lambda cfm, adapter, **kw: captured.update(kw) or ([], 0, 0, 0, 0),
        )
        handler = BCPHandler()
        handler._measure_fps(cfm, MagicMock())
        assert captured["include_evidence"] is True
        captured["record_request"]()
        requests.add.assert_called_once_with(1)
        captured["record_success"](3.5)
        duration.record.assert_called_once_with(3.5)
        captured["record_error"](2)
        errors.add.assert_called_once_with(2)

    def test_measure_fps_callbacks_when_telemetry_none(
        self, cfm: CanonicalFunctionalModel, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(bcp_plugin_module, "_sdk_requests", None)
        monkeypatch.setattr(bcp_plugin_module, "_sdk_duration", None)
        monkeypatch.setattr(bcp_plugin_module, "_sdk_errors", None)
        captured: dict[str, object] = {}
        monkeypatch.setattr(
            bcp_plugin_module,
            "measure_all",
            lambda cfm, adapter, **kw: captured.update(kw) or ([], 0, 0, 0, 0),
        )
        handler = BCPHandler()
        handler._measure_fps(cfm, MagicMock())
        assert captured["include_evidence"] is True
        assert captured["record_request"]() is None
        assert captured["record_success"](1.0) is None
        assert captured["record_error"](1) is None


class TestBCPPlugin:
    def test_plugin_properties(self) -> None:
        p = BCPPlugin()
        assert p.plugin_id() == "bcp"
        assert p.supported_methodology() == "BCP"
        assert p.supported_component_types() == ["functional_process"]

    def test_measure_delegates_with_provider(self, monkeypatch: pytest.MonkeyPatch) -> None:
        p = BCPPlugin()
        called: dict[str, object] = {}
        monkeypatch.setattr(
            BCPPlugin,
            "_handler_measure",
            staticmethod(lambda cfm, provider=None: called.update(provider=provider) or MagicMock()),
        )
        p.measure(_make_cfm(), provider="anthropic")
        assert called["provider"] == "anthropic"

    def test_measure_delegates_without_provider(self, monkeypatch: pytest.MonkeyPatch) -> None:
        p = BCPPlugin()
        called: dict[str, object] = {}
        monkeypatch.setattr(
            BCPPlugin,
            "_handler_measure",
            staticmethod(lambda cfm, provider=None: called.update(provider=provider) or MagicMock()),
        )
        p.measure(_make_cfm())
        assert called["provider"] is None

    def test_handler_measure_missing_cfm(self) -> None:
        result = BCPPlugin._handler_measure(None, "openai")
        assert result.run_id
        assert result.run_id != "None"
        assert result.total_bcp == 0.0
        assert result.items == []
        assert result.execution_metadata.duration_ms == 0.0
        assert result.execution_metadata.total_fps_processed == 0
        assert len(result.warnings) == 1
        assert result.warnings[0].code == "MISSING_CFM"
        assert result.warnings[0].message == "CFM not available."

    def test_handler_measure_default_provider(self, monkeypatch: pytest.MonkeyPatch) -> None:
        adapter = MagicMock()
        adapter.is_available = False
        adapter._import_error = None
        monkeypatch.setattr(bcp_plugin_module, "BcpSdkAdapter", lambda provider: adapter)
        monkeypatch.delenv("BCP_PROVIDER", raising=False)
        result = BCPPlugin._handler_measure(_make_cfm())
        assert result.provider == "openai"
        assert result.warnings[0].code == "SDK_NOT_AVAILABLE"
        assert result.warnings[0].message == "BCP SDK not available."

    def test_handler_measure_provider_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        adapter = MagicMock()
        adapter.is_available = True
        adapter._import_error = None
        monkeypatch.setattr(bcp_plugin_module, "BcpSdkAdapter", lambda provider: adapter)
        monkeypatch.setattr(
            bcp_plugin_module,
            "measure_all",
            lambda cfm, adapter, **kw: (
                [_make_success_item(), _make_failed_item()],
                1,
                1,
                2,
                0,
            ),
        )
        monkeypatch.setenv("BCP_PROVIDER", "anthropic")
        result = BCPPlugin._handler_measure(_make_cfm())
        assert result.provider == "anthropic"

    def test_handler_measure_sdk_not_available(
        self, cfm: CanonicalFunctionalModel, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        adapter = MagicMock()
        adapter.is_available = False
        adapter._import_error = None
        monkeypatch.setattr(bcp_plugin_module, "BcpSdkAdapter", lambda provider: adapter)
        result = BCPPlugin._handler_measure(cfm, "openai")
        assert result.provider == "openai"
        assert result.total_bcp == 0.0
        assert result.items == []
        assert result.execution_metadata.duration_ms == 0.0
        assert result.execution_metadata.total_fps_processed == 0
        assert result.warnings[0].code == "SDK_NOT_AVAILABLE"
        assert result.warnings[0].message == "BCP SDK not available."

    def test_handler_measure_success(
        self, cfm: CanonicalFunctionalModel, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        adapter = MagicMock()
        adapter.is_available = True
        adapter._import_error = None
        monkeypatch.setattr(bcp_plugin_module, "BcpSdkAdapter", lambda provider: adapter)
        monkeypatch.setattr(
            bcp_plugin_module,
            "measure_all",
            lambda cfm, adapter, **kw: (
                [_make_success_item(), _make_failed_item()],
                1,
                1,
                2,
                3,
            ),
        )
        result = BCPPlugin._handler_measure(cfm, "anthropic")
        assert result.run_id
        assert result.run_id != "None"
        assert result.provider == "anthropic"
        assert result.total_bcp == 10.0
        assert len(result.items) == 2
        assert result.execution_metadata.total_fps_processed == 2
        assert result.execution_metadata.items_succeeded == 1
        assert result.execution_metadata.items_failed == 1
        assert result.execution_metadata.sdk_call_count == 2
        assert result.execution_metadata.sdk_errors == 3
        assert result.warnings == []

    def test_handler_measure_adapter_provider_and_include_evidence(
        self, cfm: CanonicalFunctionalModel, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        adapter = MagicMock()
        adapter.is_available = True
        adapter._import_error = None
        created: list[str] = []
        def factory(provider):
            created.append(provider)
            return adapter
        monkeypatch.setattr(bcp_plugin_module, "BcpSdkAdapter", factory)
        captured: dict[str, object] = {}
        monkeypatch.setattr(
            bcp_plugin_module,
            "measure_all",
            lambda cfm, adapter, **kw: captured.update(kw) or (
                [_make_success_item(), _make_failed_item()],
                1,
                1,
                2,
                0,
            ),
        )
        monkeypatch.setenv("BCP_PROVIDER", "anthropic")
        BCPPlugin._handler_measure(cfm)
        assert created == ["anthropic"]
        assert captured["include_evidence"] is False
