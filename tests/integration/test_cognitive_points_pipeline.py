from __future__ import annotations

import uuid

from specmetrics.kernel.cfm.model import (
    BuildMetadata as CfmBuildMetadata,
)
from specmetrics.kernel.cfm.model import (
    CanonicalFunctionalModel,
    FunctionalProcess,
    Operation,
)
from specmetrics.kernel.cfm.model import (
    EvidenceRef as CfmEvidenceRef,
)
from specmetrics.kernel.csm.model import (
    BuildMetadata as CsmBuildMetadata,
)
from specmetrics.kernel.csm.model import (
    CanonicalSpecificationModel,
    Decision,
    SpecificationActivity,
)
from specmetrics.kernel.csm.model import (
    EvidenceRef as CsmEvidenceRef,
)
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.plugins.measurement.cognitive_points.plugin import (
    CognitivePointsHandler,
)


def _uid() -> str:
    return str(uuid.uuid4())


def _make_cfm() -> CanonicalFunctionalModel:
    ev = CfmEvidenceRef(graph_node_id="gn-001", document_id="doc-001", text="ev")
    return CanonicalFunctionalModel(
        run_id="pipeline-test-cfm",
        functional_processes={
            _uid(): FunctionalProcess(id=_uid(), name="Login", evidence=ev),
        },
        operations={
            _uid(): Operation(
                id=_uid(),
                name="Authenticate",
                parent_process_id=_uid(),
                evidence=ev,
            ),
        },
        metadata=CfmBuildMetadata(
            run_id="pipeline-test-cfm", version="1.0", source="test"
        ),
    )


def _make_csm() -> CanonicalSpecificationModel:
    ev = CsmEvidenceRef(graph_node_id="gn-002", document_id="doc-001", text="ev")
    return CanonicalSpecificationModel(
        run_id="pipeline-test-csm",
        specification_activities={
            _uid(): SpecificationActivity(
                id=_uid(),
                description="Clarification",
                activity_type="clarification",
                evidence_references=[ev],
            ),
        },
        decisions={
            _uid(): Decision(
                id=_uid(),
                description="Use Python",
                evidence_references=[ev],
            ),
        },
        metadata=CsmBuildMetadata(
            run_id="pipeline-test-csm", version="1.0", source="test"
        ),
    )


class TestCognitivePointsPipeline:
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
        handler = CognitivePointsHandler()
        result_ctx = handler.handle(event)

        assert result_ctx is not None
        assert result_ctx.measurement_result is not None
        payload = result_ctx.measurement_result
        assert "cognitive_total_cognitive_points" in payload
        assert "cognitive_raw_score" in payload
        assert "cognitive_specification_review_effort" in payload
        assert "cognitive_functional_validation_effort" in payload
        assert "cognitive_element_counts" in payload
        assert "cognitive_duration_ms" in payload
        assert payload["cognitive_total_cognitive_points"] > 0
        assert payload["cognitive_raw_score"] > 0
        assert payload["cognitive_specification_review_effort"]["total_raw"] > 0
        assert payload["cognitive_functional_validation_effort"]["total_raw"] > 0

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
        handler = CognitivePointsHandler()
        result_ctx = handler.handle(event)
        payload = result_ctx.measurement_result
        assert payload["cognitive_specification_review_effort"]["total_raw"] == 0
        assert payload["cognitive_functional_validation_effort"]["total_raw"] > 0
        assert len(payload["cognitive_warnings"]) > 0

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
        handler = CognitivePointsHandler()
        result_ctx = handler.handle(event)
        payload = result_ctx.measurement_result
        assert payload["cognitive_functional_validation_effort"]["total_raw"] == 0
        assert payload["cognitive_specification_review_effort"]["total_raw"] > 0

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
        handler = CognitivePointsHandler()
        result_ctx = handler.handle(event)
        payload = result_ctx.measurement_result
        assert payload["cognitive_total_cognitive_points"] == 1
        assert payload["cognitive_raw_score"] == 0

    def test_payload_contains_bloom_breakdown(self):
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
        handler = CognitivePointsHandler()
        result_ctx = handler.handle(event)
        payload = result_ctx.measurement_result

        assert "cognitive_bloom_breakdown" in payload
        bd = payload["cognitive_bloom_breakdown"]
        assert isinstance(bd, dict)
        assert len(bd) > 0
        for data in bd.values():
            assert isinstance(data, dict)
            assert "total" in data
            assert isinstance(data["total"], float)

        bd_total = sum(v["total"] for v in bd.values())
        assert abs(bd_total - payload["cognitive_raw_score"]) < 0.01

    def test_payload_bloom_breakdown_empty_when_no_elements(self):
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
        handler = CognitivePointsHandler()
        result_ctx = handler.handle(event)
        payload = result_ctx.measurement_result

        assert "cognitive_bloom_breakdown" in payload
        assert payload["cognitive_bloom_breakdown"] == {}
