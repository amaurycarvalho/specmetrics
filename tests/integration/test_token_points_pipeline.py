from __future__ import annotations

import uuid

from specmetrics.kernel.cfm.model import (
    CanonicalFunctionalModel,
    EvidenceRef as CfmEvidenceRef,
    FunctionalProcess,
    Operation,
    BuildMetadata as CfmBuildMetadata,
)
from specmetrics.kernel.csm.model import (
    CanonicalSpecificationModel,
    Decision,
    EvidenceRef as CsmEvidenceRef,
    SpecificationActivity,
    BuildMetadata as CsmBuildMetadata,
)
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.plugins.measurement.token_points.plugin import (
    TokenPointsHandler,
)


def _uid() -> str:
    return str(uuid.uuid4())


def _make_cfm() -> CanonicalFunctionalModel:
    ev = CfmEvidenceRef(graph_node_id="gn-001", document_id="doc-001", text="ev")
    return CanonicalFunctionalModel(
        run_id="pipeline-test-cfm",
        functional_processes={
            _uid(): FunctionalProcess(
                id=_uid(), name="Login", evidence=ev,
            ),
        },
        operations={
            _uid(): Operation(
                id=_uid(), name="Authenticate",
                parent_process_id=_uid(), evidence=ev,
            ),
        },
        metadata=CfmBuildMetadata(run_id="pipeline-test-cfm", version="1.0", source="test"),
    )


def _make_csm() -> CanonicalSpecificationModel:
    ev = CsmEvidenceRef(graph_node_id="gn-002", document_id="doc-001", text="ev")
    return CanonicalSpecificationModel(
        run_id="pipeline-test-csm",
        specification_activities={
            _uid(): SpecificationActivity(
                id=_uid(), description="Clarification",
                activity_type="clarification", evidence_references=[ev],
            ),
        },
        decisions={
            _uid(): Decision(
                id=_uid(), description="Use Python",
                evidence_references=[ev],
            ),
        },
        metadata=CsmBuildMetadata(run_id="pipeline-test-csm", version="1.0", source="test"),
    )


class TestTokenPointsPipeline:
    def test_pipeline_integration(self):
        cfm = _make_cfm()
        csm = _make_csm()
        ctx = PipelineContext(
            canonical_model=cfm,
            canonical_spec_model=csm,
        )
        event = PipelineEvent(
            event_type=EventType.MEASUREMENT_COMPLETED,
            publisher="test",
            payload={},
            context=ctx,
        )
        handler = TokenPointsHandler()
        result_ctx = handler.handle(event)

        assert result_ctx is not None
        assert result_ctx.measurement_result is not None
        payload = result_ctx.measurement_result
        assert "total_score" in payload
        assert "specification_cost" in payload
        assert "code_generation_cost" in payload
        assert "element_counts" in payload
        assert "duration_ms" in payload
        assert payload["total_score"] > 0
        assert payload["specification_cost"] > 0
        assert payload["code_generation_cost"] > 0

    def test_pipeline_missing_csm(self):
        cfm = _make_cfm()
        ctx = PipelineContext(
            canonical_model=cfm,
            canonical_spec_model=None,
        )
        event = PipelineEvent(
            event_type=EventType.MEASUREMENT_COMPLETED,
            publisher="test",
            payload={},
            context=ctx,
        )
        handler = TokenPointsHandler()
        result_ctx = handler.handle(event)
        payload = result_ctx.measurement_result
        assert payload["specification_cost"] == 0
        assert payload["code_generation_cost"] > 0
        assert len(payload["warnings"]) > 0

    def test_pipeline_missing_cfm(self):
        csm = _make_csm()
        ctx = PipelineContext(
            canonical_model=None,
            canonical_spec_model=csm,
        )
        event = PipelineEvent(
            event_type=EventType.MEASUREMENT_COMPLETED,
            publisher="test",
            payload={},
            context=ctx,
        )
        handler = TokenPointsHandler()
        result_ctx = handler.handle(event)
        payload = result_ctx.measurement_result
        assert payload["code_generation_cost"] == 0
        assert payload["specification_cost"] > 0

    def test_pipeline_both_missing(self):
        ctx = PipelineContext(
            canonical_model=None,
            canonical_spec_model=None,
        )
        event = PipelineEvent(
            event_type=EventType.MEASUREMENT_COMPLETED,
            publisher="test",
            payload={},
            context=ctx,
        )
        handler = TokenPointsHandler()
        result_ctx = handler.handle(event)
        payload = result_ctx.measurement_result
        assert payload["total_score"] == 0
