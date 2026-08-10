from __future__ import annotations

from unittest.mock import MagicMock, patch

from specmetrics.kernel.cfm.model import (
    BuildMetadata,
    CanonicalFunctionalModel,
    EvidenceRef,
    FunctionalProcess,
)
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.plugins.measurement.bcp.plugin import BCPHandler


def _make_cfm() -> CanonicalFunctionalModel:
    ev = EvidenceRef(graph_node_id="gn-001", document_id="doc-001", text="ev")
    return CanonicalFunctionalModel(
        run_id="pipeline-test",
        functional_processes={
            "fp-001": FunctionalProcess(id="fp-001", name="Login", evidence=ev),
        },
        metadata=BuildMetadata(run_id="pipeline-test", version="1.0", source="test"),
    )


class TestBCPPipeline:
    def test_pipeline_integration(self):
        cfm = _make_cfm()
        ctx = PipelineContext(canonical_model=cfm)
        event = PipelineEvent(
            event_type=EventType.MEASUREMENT_COMPLETED,
            publisher="test",
            payload={},
            context=ctx,
        )

        mock_adapter = MagicMock()
        mock_adapter.is_available = True
        mock_adapter.calculate.return_value.total_bcp = 15.0
        mock_adapter.calculate.return_value.breakdown = {}
        mock_adapter.calculate.return_value.errors = []
        mock_adapter.calculate.return_value.raw_response = {}
        mock_adapter.calculate.return_value.duration_ms = 100.0

        with patch(
            "specmetrics.plugins.measurement.bcp.plugin.BcpSdkAdapter",
            return_value=mock_adapter,
        ), patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
            handler = BCPHandler()
            result_ctx = handler.handle(event)

        assert result_ctx is not None
        assert result_ctx.measurement_result is not None
        payload = result_ctx.measurement_result
        assert "bcp_method" in payload
        assert payload["bcp_method"] == "BCP"
        assert "bcp_total_bcp" in payload
        assert payload["bcp_total_bcp"] > 0

    def test_pipeline_missing_cfm(self):
        ctx = PipelineContext(canonical_model=None)
        event = PipelineEvent(
            event_type=EventType.MEASUREMENT_COMPLETED,
            publisher="test",
            payload={},
            context=ctx,
        )
        handler = BCPHandler()
        result_ctx = handler.handle(event)
        payload = result_ctx.measurement_result
        assert payload["bcp_total_bcp"] == 0
        assert len(payload["bcp_warnings"]) > 0
