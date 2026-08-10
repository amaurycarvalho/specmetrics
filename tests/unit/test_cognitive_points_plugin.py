from __future__ import annotations

from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.plugins.measurement.cognitive_points.calibration import (
    CognitiveCalibrationProfile,
)
from specmetrics.plugins.measurement.cognitive_points.plugin import (
    CognitivePointsHandler,
    create_cognitive_points_measurement_metadata,
)


def _empty_cfm():
    from specmetrics.kernel.cfm.metadata import BuildMetadata
    from specmetrics.kernel.cfm.model import CanonicalFunctionalModel

    return CanonicalFunctionalModel(
        run_id="p-cfm",
        metadata=BuildMetadata(run_id="p-cfm", version="1.0", source="test"),
    )


def _cfm_with_actor():
    from specmetrics.kernel.cfm.metadata import BuildMetadata
    from specmetrics.kernel.cfm.model import Actor, CanonicalFunctionalModel
    from specmetrics.kernel.cfm.model import EvidenceRef as CfmEvidenceRef

    return CanonicalFunctionalModel(
        run_id="p-cfm-actor",
        actors={
            "actor-1": Actor(
                id="actor-1",
                name="",
                actor_type="person",
                evidence=CfmEvidenceRef(
                    graph_node_id="gn-1", document_id="doc-1", text="t"
                ),
            ),
        },
        metadata=BuildMetadata(run_id="p-cfm-actor", version="1.0", source="test"),
    )


def _cfm_with_process():
    from specmetrics.kernel.cfm.metadata import BuildMetadata
    from specmetrics.kernel.cfm.model import CanonicalFunctionalModel, FunctionalProcess
    from specmetrics.kernel.cfm.model import EvidenceRef as CfmEvidenceRef

    return CanonicalFunctionalModel(
        run_id="p-cfm-proc",
        functional_processes={
            "fp-1": FunctionalProcess(
                id="fp-1",
                name="Login",
                description="Authenticate user",
                actor_ids=[],
                operation_ids=[],
                evidence=CfmEvidenceRef(
                    graph_node_id="d-1", document_id="doc-1", text="t"
                ),
            ),
        },
        metadata=BuildMetadata(run_id="p-cfm-proc", version="1.0", source="test"),
    )


def _event(measurement_result=None, metadata=None) -> PipelineEvent:
    ctx = PipelineContext(measurement_result=measurement_result, metadata=metadata)
    return PipelineEvent(
        event_type=EventType.MEASUREMENT_COMPLETED,
        publisher="cognitive_points",
        payload={},
        context=ctx,
    )


class TestHandlerIdentity:
    def test_handler_id(self):
        assert (
            CognitivePointsHandler().handler_id == "cognitive_points_measurement"
        )

    def test_handled_event_type(self):
        assert (
            CognitivePointsHandler().handled_event_type
            == EventType.MEASUREMENT_COMPLETED
        )

    def test_stage_name(self):
        assert (
            CognitivePointsHandler().stage_name
            == "Cognitive Points Measurement"
        )


class TestResolveCalibration:
    def test_returns_profile_when_metadata_is_profile(self):
        profile = CognitiveCalibrationProfile()
        ctx = PipelineContext(metadata=profile)
        result = CognitivePointsHandler()._resolve_calibration(ctx)
        assert result is profile

    def test_returns_default_when_metadata_is_not_profile(self):
        ctx = PipelineContext(metadata={"content_multiplier": 0.2})
        result = CognitivePointsHandler()._resolve_calibration(ctx)
        from specmetrics.plugins.measurement.cognitive_points.calibration import (
            get_default_calibration,
        )

        assert result == get_default_calibration()

    def test_returns_default_when_metadata_none(self):
        result = CognitivePointsHandler()._resolve_calibration(
            PipelineContext(metadata=None)
        )
        assert result is not None


class TestHandleNoModels:
    def test_handle_empty_returns_payload(self):
        ctx = CognitivePointsHandler().handle(_event())
        payload = ctx.measurement_result
        assert "cognitive_total_cognitive_points" in payload
        assert isinstance(payload["cognitive_total_cognitive_points"], (int, float))
        assert "cognitive_entities" in payload
        assert payload["cognitive_bloom_breakdown"] == {}
        assert payload["cognitive_entities"] == []

    def test_handle_payload_exact_keys(self):
        from specmetrics.kernel.events import EventType, PipelineEvent

        ctx = PipelineContext(
            canonical_model=_cfm_with_process(),
            canonical_spec_model=None,
        )
        event = PipelineEvent(
            event_type=EventType.MEASUREMENT_COMPLETED,
            publisher="cognitive_points",
            payload={},
            context=ctx,
        )
        out = CognitivePointsHandler().handle(event)
        payload = out.measurement_result
        assert len(out.published_events) == 1
        ev = out.published_events[0]
        assert ev.event_type == EventType.COGNITIVE_POINTS_MEASURED
        assert ev.publisher == "cognitive_points"
        assert ev.context is ctx
        assert ev.payload["cognitive_total_cognitive_points"] == payload[
            "cognitive_total_cognitive_points"
        ]
        assert set(payload.keys()) == {
            "cognitive_total_cognitive_points",
            "cognitive_raw_score",
            "cognitive_specification_review_effort",
            "cognitive_functional_validation_effort",
            "cognitive_fibonacci_normalization",
            "cognitive_content_multiplier",
            "cognitive_content_tokens",
            "cognitive_element_counts",
            "cognitive_bloom_distribution",
            "cognitive_calibration_version",
            "cognitive_duration_ms",
            "cognitive_warnings",
            "cognitive_entities",
            "cognitive_bloom_breakdown",
        }
        fib = payload["cognitive_fibonacci_normalization"]
        assert set(fib.keys()) == {"raw_score", "threshold", "output"}
        spec = payload["cognitive_specification_review_effort"]
        assert set(spec.keys()) == {"total_raw", "bloom_breakdown"}
        func = payload["cognitive_functional_validation_effort"]
        assert set(func.keys()) == {"total_raw", "bloom_breakdown"}
        assert spec["bloom_breakdown"] == {}
        assert func["bloom_breakdown"] == {"create": 1}
        assert isinstance(payload["cognitive_bloom_distribution"], dict)
        counts = payload["cognitive_element_counts"]
        assert set(counts.keys()) == {"csm", "cfm", "total"}
        assert payload["cognitive_element_counts"] == {
            "csm": 0,
            "cfm": 1,
            "total": 1,
        }

    def test_handle_content_tokens_exact(self):
        from specmetrics.kernel.events import EventType, PipelineEvent

        ctx = PipelineContext(canonical_model=_cfm_with_process())
        event = PipelineEvent(
            event_type=EventType.MEASUREMENT_COMPLETED,
            publisher="cognitive_points",
            payload={},
            context=ctx,
        )
        payload = CognitivePointsHandler().handle(event).measurement_result
        tokens = payload["cognitive_content_tokens"]
        assert set(tokens.keys()) == {"functional_processes"}
        assert tokens["functional_processes"] == payload["cognitive_entities"][0][
            "content_token_count"
        ]

    def test_handle_uses_custom_calibration(self):
        from specmetrics.kernel.events import EventType, PipelineEvent

        cal = CognitiveCalibrationProfile(content_multiplier=0.5)
        ctx = PipelineContext(
            canonical_model=_cfm_with_process(),
            metadata=cal,
        )
        event = PipelineEvent(
            event_type=EventType.MEASUREMENT_COMPLETED,
            publisher="cognitive_points",
            payload={},
            context=ctx,
        )
        payload = CognitivePointsHandler().handle(event).measurement_result
        assert payload["cognitive_content_multiplier"] == 0.5

    def test_handle_single_point_remember_included(self):
        from specmetrics.kernel.events import EventType, PipelineEvent

        ctx = PipelineContext(canonical_model=_cfm_with_actor())
        event = PipelineEvent(
            event_type=EventType.MEASUREMENT_COMPLETED,
            publisher="cognitive_points",
            payload={},
            context=ctx,
        )
        payload = CognitivePointsHandler().handle(event).measurement_result
        assert payload["cognitive_bloom_breakdown"] == {"remember": {"total": 1.0}}


class TestPluginMetadata:
    def test_metadata_exact(self):
        meta = create_cognitive_points_measurement_metadata()
        assert meta.id == "cognitive_points"
        assert meta.api_version == "0.1.0"
        assert meta.version == "0.1.0"
        assert meta.plugin_type.value == "measurement"
        assert meta.name == "Cognitive Points"
        assert meta.handled_event_types == (EventType.MEASUREMENT_COMPLETED,)
        assert meta.handler_factory() is not None
        assert meta.description == (
            "Cognitive Points measurement — estimates human cognitive effort "
            "from CFM and CSM using Bloom taxonomy and Fibonacci normalization"
        )