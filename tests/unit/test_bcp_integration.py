from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

from specmetrics.kernel.cfm.model import (
    Actor,
    CanonicalFunctionalModel,
    EvidenceRef,
    FunctionalProcess,
    BuildMetadata,
)
from specmetrics.plugins.measurement.bcp.models import BCPMeasurementResult
from specmetrics.plugins.measurement.bcp.plugin import BCPPlugin


def _uid() -> str:
    return str(uuid.uuid4())


def _make_cfm() -> CanonicalFunctionalModel:
    ev = EvidenceRef(
        graph_node_id="gn-001", document_id="doc-001", text="ev"
    )
    fp1_id = _uid()
    fp2_id = _uid()
    return CanonicalFunctionalModel(
        run_id="test-cfm",
        actors={
            _uid(): Actor(id=_uid(), name="User", evidence=ev),
        },
        functional_processes={
            fp1_id: FunctionalProcess(
                id=fp1_id,
                name="Login",
                actor_ids=[],
                evidence=ev,
            ),
            fp2_id: FunctionalProcess(
                id=fp2_id,
                name="Process Order",
                actor_ids=[],
                evidence=ev,
            ),
        },
        metadata=BuildMetadata(
            run_id="test-cfm", version="1.0", source="test"
        ),
    )


class TestFullMeasurementFlow:
    def test_full_measurement_flow(self):
        plugin = BCPPlugin()
        cfm = _make_cfm()

        mock_adapter = MagicMock()
        mock_adapter.is_available = True
        mock_adapter.calculate.return_value.total_bcp = 12.5
        mock_adapter.calculate.return_value.breakdown = {"bl": 8.0, "data": 4.5}
        mock_adapter.calculate.return_value.errors = []
        mock_adapter.calculate.return_value.raw_response = {}

        with patch(
            "specmetrics.plugins.measurement.bcp.plugin.BcpSdkAdapter",
            return_value=mock_adapter,
        ):
            with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
                result = plugin.measure(cfm)

        assert isinstance(result, BCPMeasurementResult)
        assert result.total_bcp == 25.0
        assert len(result.items) == 2
        for item in result.items:
            assert item.status == "success"
            assert "User Story" in item.generated_story

    def test_missing_cfm(self):
        plugin = BCPPlugin()
        result = plugin.measure(None)
        assert result.total_bcp == 0.0
        assert len(result.items) == 0

    def test_missing_sdk(self):
        plugin = BCPPlugin()
        cfm = _make_cfm()

        mock_adapter = MagicMock()
        mock_adapter.is_available = False
        mock_adapter._import_error = "SDK not installed"

        with patch(
            "specmetrics.plugins.measurement.bcp.plugin.BcpSdkAdapter",
            return_value=mock_adapter,
        ):
            result = plugin.measure(cfm)

        assert result.total_bcp == 0.0
        assert len(result.items) == 0
