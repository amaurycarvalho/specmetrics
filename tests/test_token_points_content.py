from __future__ import annotations

import uuid

from specmetrics.kernel.cfm.model import (
    Actor,
    CanonicalFunctionalModel,
    FunctionalProcess,
    Operation,
)
from specmetrics.kernel.cfm.model import (
    BuildMetadata as CfmBuildMetadata,
)
from specmetrics.kernel.cfm.model import (
    EvidenceRef as CfmEvidenceRef,
)
from specmetrics.kernel.csm.model import (
    Assumption,
    CanonicalSpecificationModel,
    Decision,
    Reference,
    SpecificationActivity,
)
from specmetrics.kernel.csm.model import (
    BuildMetadata as CsmBuildMetadata,
)
from specmetrics.kernel.csm.model import (
    EvidenceRef as CsmEvidenceRef,
)
from specmetrics.plugins.calibration.models import (
    CalibrationProfile,
    CodeGenerationCostWeights,
    SpecificationCostWeights,
)
from specmetrics.plugins.measurement.token_points.calculator import (
    calculate,
    count_tokens,
)


def _uid() -> str:
    return str(uuid.uuid4())


def _make_cfm_evidence() -> CfmEvidenceRef:
    return CfmEvidenceRef(
        graph_node_id="gn-cfm-001", document_id="doc-001", text="cfm evidence"
    )


def _make_csm_evidence() -> CsmEvidenceRef:
    return CsmEvidenceRef(
        graph_node_id="gn-csm-001", document_id="doc-001", text="csm evidence"
    )


def _make_default_calibration() -> CalibrationProfile:
    return CalibrationProfile(
        version="1.0",
        specification_cost=SpecificationCostWeights(),
        code_generation_cost=CodeGenerationCostWeights(),
    )


def _make_cfm_with_descriptions(desc_len: int) -> CanonicalFunctionalModel:
    ev = _make_cfm_evidence()
    text = "word " * desc_len
    return CanonicalFunctionalModel(
        run_id="cfm-content",
        functional_processes={
            _uid(): FunctionalProcess(
                id=_uid(),
                name="Process A",
                description=text,
                actor_ids=[],
                operation_ids=[],
                evidence=ev,
            ),
        },
        operations={
            _uid(): Operation(
                id=_uid(),
                name="Op A",
                description=text,
                parent_process_id=_uid(),
                evidence=ev,
            ),
        },
        actors={
            _uid(): Actor(id=_uid(), name="Actor A", actor_type="person", evidence=ev),
        },
        metadata=CfmBuildMetadata(run_id="cfm-content", version="1.0", source="test"),
    )


def _make_csm_with_descriptions(desc_len: int) -> CanonicalSpecificationModel:
    ev = _make_csm_evidence()
    text = "word " * desc_len
    return CanonicalSpecificationModel(
        run_id="csm-content",
        specification_activities={
            _uid(): SpecificationActivity(
                id=_uid(),
                description=text,
                activity_type="exploration",
                evidence_references=[ev],
            ),
        },
        decisions={
            _uid(): Decision(id=_uid(), description=text, evidence_references=[ev]),
        },
        metadata=CsmBuildMetadata(run_id="csm-content", version="1.0", source="test"),
    )


class TestCountTokens:
    def test_count_tokens_known_text(self):
        text = "Hello, world! This is a test."
        n = count_tokens(text)
        assert isinstance(n, int)
        assert n > 0

    def test_count_tokens_empty_string(self):
        n = count_tokens("")
        assert n >= 0

    def test_count_tokens_long_text(self):
        text = "token " * 500
        n = count_tokens(text)
        assert n > 0


class TestContentBasedScoring:
    def test_longer_description_scores_higher(self):
        short_desc = "word"
        long_desc = "word " * 1000

        ev = _make_cfm_evidence()
        cfm = CanonicalFunctionalModel(
            run_id="cfm-compare",
            functional_processes={
                _uid(): FunctionalProcess(
                    id=_uid(),
                    name="Short",
                    description=short_desc,
                    actor_ids=[],
                    operation_ids=[],
                    evidence=ev,
                ),
            },
            metadata=CfmBuildMetadata(
                run_id="cfm-compare", version="1.0", source="test"
            ),
        )

        cal = _make_default_calibration()
        short_result = calculate(cfm, None, cal, run_id="test-short")

        cfm2 = CanonicalFunctionalModel(
            run_id="cfm-compare-2",
            functional_processes={
                _uid(): FunctionalProcess(
                    id=_uid(),
                    name="Long",
                    description=long_desc,
                    actor_ids=[],
                    operation_ids=[],
                    evidence=ev,
                ),
            },
            metadata=CfmBuildMetadata(
                run_id="cfm-compare-2", version="1.0", source="test"
            ),
        )
        long_result = calculate(cfm2, None, cal, run_id="test-long")

        assert long_result.total_score > short_result.total_score

    def test_content_token_count_populated(self):
        ev = _make_csm_evidence()
        csm = CanonicalSpecificationModel(
            run_id="csm-content-check",
            decisions={
                _uid(): Decision(
                    id=_uid(),
                    description="Test decision with some content for token counting",
                    evidence_references=[ev],
                ),
            },
            metadata=CsmBuildMetadata(
                run_id="csm-content-check", version="1.0", source="test"
            ),
        )
        cal = _make_default_calibration()
        result = calculate(None, csm, cal, run_id="test-ctc")
        for contrib in result.specification_cost.contributions:
            assert contrib.content_token_count > 0
            assert contrib.content_score > 0.0
            assert (
                contrib.partial_score == contrib.applied_weight + contrib.content_score
            )

    def test_empty_content_gets_zero_content_score(self):
        ev = _make_cfm_evidence()
        cfm = CanonicalFunctionalModel(
            run_id="cfm-empty",
            functional_processes={
                _uid(): FunctionalProcess(
                    id=_uid(),
                    name="",
                    description="",
                    actor_ids=[],
                    operation_ids=[],
                    evidence=ev,
                ),
            },
            metadata=CfmBuildMetadata(run_id="cfm-empty", version="1.0", source="test"),
        )
        cal = _make_default_calibration()
        result = calculate(cfm, None, cal, run_id="test-empty")
        for contrib in result.code_generation_cost.contributions:
            assert contrib.content_token_count == 0
            assert contrib.content_score == 0.0
            assert contrib.partial_score == contrib.applied_weight

    def test_csm_references_contribute_score(self):
        ev = _make_csm_evidence()
        csm = CanonicalSpecificationModel(
            run_id="csm-refs",
            references={
                _uid(): Reference(
                    id=_uid(),
                    description="RFC-1234: API Specification",
                    evidence_references=[ev],
                ),
            },
            metadata=CsmBuildMetadata(run_id="csm-refs", version="1.0", source="test"),
        )
        cal = _make_default_calibration()
        result = calculate(None, csm, cal, run_id="test-refs")
        ref_contribs = [
            c
            for c in result.specification_cost.contributions
            if c.element_type == "references"
        ]
        assert len(ref_contribs) == 1
        assert ref_contribs[0].partial_score > 0

    def test_content_multiplier_zero_disables_content(self):
        ev = _make_cfm_evidence()
        cfm = CanonicalFunctionalModel(
            run_id="cfm-zero-mult",
            functional_processes={
                _uid(): FunctionalProcess(
                    id=_uid(),
                    name="Test",
                    description="A long description that would normally add content score",
                    actor_ids=[],
                    operation_ids=[],
                    evidence=ev,
                ),
            },
            metadata=CfmBuildMetadata(
                run_id="cfm-zero-mult", version="1.0", source="test"
            ),
        )
        cal = CalibrationProfile(
            version="1.0",
            specification_cost=SpecificationCostWeights(),
            code_generation_cost=CodeGenerationCostWeights(),
            content_multiplier=0.0,
        )
        result = calculate(cfm, None, cal, run_id="test-mult-zero")
        for contrib in result.code_generation_cost.contributions:
            assert contrib.content_score == 0.0
            assert contrib.partial_score == contrib.applied_weight


class TestCrossSpecComparability:
    def test_2to1_content_volume_ratio(self):
        ev = _make_cfm_evidence()
        cal = _make_default_calibration()

        short_text = "word " * 100
        long_text = "word " * 200

        small_cfm = CanonicalFunctionalModel(
            run_id="cfm-small",
            functional_processes={
                _uid(): FunctionalProcess(
                    id=_uid(),
                    name="Small",
                    description=short_text,
                    actor_ids=[],
                    operation_ids=[],
                    evidence=ev,
                ),
            },
            metadata=CfmBuildMetadata(run_id="cfm-small", version="1.0", source="test"),
        )
        large_cfm = CanonicalFunctionalModel(
            run_id="cfm-large",
            functional_processes={
                _uid(): FunctionalProcess(
                    id=_uid(),
                    name="Large",
                    description=long_text,
                    actor_ids=[],
                    operation_ids=[],
                    evidence=ev,
                ),
            },
            metadata=CfmBuildMetadata(run_id="cfm-large", version="1.0", source="test"),
        )

        small_result = calculate(small_cfm, None, cal, run_id="test-small")
        large_result = calculate(large_cfm, None, cal, run_id="test-large")

        ratio = large_result.total_score / small_result.total_score
        assert 1.5 <= ratio <= 2.5, (
            f"Expected ratio between 1.5 and 2.5 for ~2:1 content volume, got {ratio:.2f}"
        )


class TestCalibrationBackwardCompatibility:
    def test_old_yaml_without_content_multiplier_defaults(self):
        data = {
            "version": "1.0",
            "specification_cost": {
                "decisions": 2.0,
            },
            "code_generation_cost": {
                "functional_processes": 10.0,
            },
        }
        from specmetrics.plugins.calibration.loader import merge_calibration_data

        default = _make_default_calibration()
        merged = merge_calibration_data(default, data)
        assert merged.content_multiplier == 0.1
        assert merged.specification_cost.decisions == 2.0
        assert merged.code_generation_cost.functional_processes == 10.0

    def test_old_yaml_without_activities_defaults_nonzero(self):
        data = {
            "version": "1.0",
            "specification_cost": {},
            "code_generation_cost": {},
        }
        from specmetrics.plugins.calibration.loader import merge_calibration_data

        default = _make_default_calibration()
        merged = merge_calibration_data(default, data)
        activity_vals = merged.specification_cost.activities
        for key in [
            "exploration",
            "clarification",
            "refinement",
            "review",
            "validation",
        ]:
            assert activity_vals.get(key, 0) > 0, f"{key} should have non-zero default"

    def test_content_multiplier_zero_makes_scores_uniform(self):
        ev = _make_cfm_evidence()
        cfm = CanonicalFunctionalModel(
            run_id="cfm-uniform",
            functional_processes={
                _uid(): FunctionalProcess(
                    id=_uid(),
                    name="Process A",
                    description="A longer description that would normally add variance",
                    actor_ids=[],
                    operation_ids=[],
                    evidence=ev,
                ),
                _uid(): FunctionalProcess(
                    id=_uid(),
                    name="Process B",
                    description="Short",
                    actor_ids=[],
                    operation_ids=[],
                    evidence=ev,
                ),
            },
            metadata=CfmBuildMetadata(
                run_id="cfm-uniform", version="1.0", source="test"
            ),
        )
        cal = CalibrationProfile(
            version="1.0",
            specification_cost=SpecificationCostWeights(),
            code_generation_cost=CodeGenerationCostWeights(),
            content_multiplier=0.0,
        )
        result = calculate(cfm, None, cal, run_id="test-uniform")
        scores = {
            c.element_name: c.partial_score
            for c in result.code_generation_cost.contributions
        }
        assert len(set(scores.values())) == 1, (
            "All same-type elements should have identical scores"
        )


class TestPayloadExtensions:
    def test_payload_contains_new_keys(self):
        from specmetrics.plugins.measurement.token_points.plugin import (
            TokenPointsHandler,
        )

        handler = TokenPointsHandler()
        ev = _make_csm_evidence()
        csm = CanonicalSpecificationModel(
            run_id="csm-payload",
            decisions={
                _uid(): Decision(
                    id=_uid(),
                    description="Some decision content",
                    evidence_references=[ev],
                ),
            },
            metadata=CsmBuildMetadata(
                run_id="csm-payload", version="1.0", source="test"
            ),
        )
        from dataclasses import replace

        from specmetrics.kernel.events import EventType, PipelineEvent
        from specmetrics.kernel.pipeline_context import PipelineContext

        ctx = replace(
            PipelineContext(),
            canonical_spec_model=csm,
            metadata=_make_default_calibration(),
        )
        event = PipelineEvent(
            event_type=EventType.MEASUREMENT_COMPLETED,
            publisher="test",
            payload={},
            context=ctx,
        )
        result_ctx = handler.handle(event)
        payload = result_ctx.measurement_result
        assert payload is not None
        assert "token_content_multiplier" in payload
        assert "token_content_tokens" in payload
        assert payload["token_content_multiplier"] == 0.1
        for entry in payload.get("token_top_contributors", []):
            assert "content_tokens" in entry

    def test_token_content_tokens_per_element_type(self):
        ev = _make_csm_evidence()
        csm = CanonicalSpecificationModel(
            run_id="csm-tct",
            decisions={
                _uid(): Decision(
                    id=_uid(),
                    description="Decision text here",
                    evidence_references=[ev],
                ),
            },
            assumptions={
                _uid(): Assumption(
                    id=_uid(),
                    description="Assumption text here",
                    evidence_references=[ev],
                ),
            },
            metadata=CsmBuildMetadata(run_id="csm-tct", version="1.0", source="test"),
        )
        cal = _make_default_calibration()
        result = calculate(None, csm, cal, run_id="test-tct")
        from specmetrics.plugins.measurement.token_points.explainer import (
            get_breakdown_by_type,
        )

        breakdown = get_breakdown_by_type(result)
        for info in breakdown.values():
            assert "content_tokens" in info
            assert info["content_tokens"] >= 0


class TestStageOutputKey:
    def test_token_content_multiplier_in_stage_output(self):
        from dataclasses import replace

        from specmetrics.kernel.events import EventType, PipelineEvent
        from specmetrics.kernel.pipeline_context import PipelineContext
        from specmetrics.plugins.measurement.token_points.plugin import (
            TokenPointsHandler,
        )

        handler = TokenPointsHandler()
        ev = _make_csm_evidence()
        csm = CanonicalSpecificationModel(
            run_id="csm-stage",
            decisions={
                _uid(): Decision(
                    id=_uid(),
                    description="Important decision",
                    evidence_references=[ev],
                ),
            },
            metadata=CsmBuildMetadata(run_id="csm-stage", version="1.0", source="test"),
        )
        ctx = replace(
            PipelineContext(),
            canonical_spec_model=csm,
            metadata=_make_default_calibration(),
        )
        event = PipelineEvent(
            event_type=EventType.MEASUREMENT_COMPLETED,
            publisher="test",
            payload={},
            context=ctx,
        )
        result_ctx = handler.handle(event)
        payload = result_ctx.measurement_result
        assert payload is not None
        assert "token_content_tokens" in payload
        assert isinstance(payload["token_content_tokens"], dict)

    def test_token_element_counts_extended(self):
        from dataclasses import replace

        from specmetrics.kernel.events import EventType, PipelineEvent
        from specmetrics.kernel.pipeline_context import PipelineContext
        from specmetrics.plugins.measurement.token_points.plugin import (
            TokenPointsHandler,
        )

        handler = TokenPointsHandler()
        csm = _make_csm_with_descriptions(50)
        ctx = replace(
            PipelineContext(),
            canonical_spec_model=csm,
            metadata=_make_default_calibration(),
        )
        event = PipelineEvent(
            event_type=EventType.MEASUREMENT_COMPLETED,
            publisher="test",
            payload={},
            context=ctx,
        )
        result_ctx = handler.handle(event)
        payload = result_ctx.measurement_result
        assert payload is not None
        for entry in payload.get("token_top_contributors", []):
            assert "content_tokens" in entry

    def test_code_blocks_tokenized_as_text(self):
        ev = _make_cfm_evidence()
        code_text = "def hello():\n    print('world')\n    return 42"
        cfm = CanonicalFunctionalModel(
            run_id="cfm-code",
            functional_processes={
                _uid(): FunctionalProcess(
                    id=_uid(),
                    name="CodeProcess",
                    description=code_text,
                    actor_ids=[],
                    operation_ids=[],
                    evidence=ev,
                ),
            },
            metadata=CfmBuildMetadata(run_id="cfm-code", version="1.0", source="test"),
        )
        cal = _make_default_calibration()
        result = calculate(cfm, None, cal, run_id="test-code-block")
        assert result.total_score > 0
        for contrib in result.code_generation_cost.contributions:
            assert contrib.content_token_count > 0


class TestExplainerBreakdown:
    def _make_measurement(self):
        from specmetrics.plugins.measurement.token_points.models import (
            CodeGenerationCost,
            MeasurementMetadata,
            SpecificationCost,
            TokenContribution,
            TokenPointsMeasurement,
        )

        def tc(element_id, element_type, model_source, weight, tokens):
            return TokenContribution(
                element_id=element_id,
                element_type=element_type,
                element_name=element_id,
                model_source=model_source,
                applied_weight=weight,
                content_token_count=tokens,
                content_score=0.0,
                partial_score=weight,
            )

        c1 = tc("1", "decision", "csm", 1.5, 10)
        c2 = tc("2", "decision", "csm", 3.5, 20)
        c3 = tc("3", "operation", "cfm", 2.0, 5)
        return TokenPointsMeasurement(
            run_id="breakdown",
            total_score=7.0,
            specification_cost=SpecificationCost(total=5.0, contributions=[c1, c2]),
            code_generation_cost=CodeGenerationCost(total=2.0, contributions=[c3]),
            measurement_metadata=MeasurementMetadata(),
        )

    def test_breakdown_by_type_exact(self):
        from specmetrics.plugins.measurement.token_points.explainer import (
            get_breakdown_by_type,
        )

        breakdown = get_breakdown_by_type(self._make_measurement())
        assert breakdown["decision"] == {
            "count": 2,
            "total": 5.0,
            "content_tokens": 30,
        }
        assert breakdown["operation"] == {
            "count": 1,
            "total": 2.0,
            "content_tokens": 5,
        }

    def test_breakdown_multiple_same_type_elements(self):
        from specmetrics.plugins.measurement.token_points.explainer import (
            get_breakdown_by_type,
        )

        breakdown = get_breakdown_by_type(self._make_measurement())
        assert breakdown["decision"]["count"] == 2
        assert breakdown["decision"]["total"] == 5.0
        assert breakdown["decision"]["content_tokens"] == 30


class TestPluginPayload:
    def test_payload_keys_and_counts(self):
        from dataclasses import replace

        from specmetrics.kernel.events import EventType, PipelineEvent
        from specmetrics.kernel.pipeline_context import PipelineContext
        from specmetrics.plugins.measurement.token_points.plugin import (
            TokenPointsHandler,
        )

        handler = TokenPointsHandler()
        ev = _make_csm_evidence()
        csm = CanonicalSpecificationModel(
            run_id="csm-payload-full",
            decisions={
                _uid(): Decision(
                    id=_uid(),
                    description="Decision content",
                    evidence_references=[ev],
                ),
                _uid(): Decision(
                    id=_uid(),
                    description="Other decision",
                    evidence_references=[ev],
                ),
            },
            metadata=CsmBuildMetadata(
                run_id="csm-payload-full", version="1.0", source="test"
            ),
        )
        ctx = replace(
            PipelineContext(),
            canonical_spec_model=csm,
            metadata=_make_default_calibration(),
        )
        event = PipelineEvent(
            event_type=EventType.MEASUREMENT_COMPLETED,
            publisher="test",
            payload={},
            context=ctx,
        )
        payload = handler.handle(event).measurement_result
        expected_keys = {
            "token_total_score",
            "token_specification_cost",
            "token_code_generation_cost",
            "token_content_multiplier",
            "token_content_tokens",
            "token_element_counts",
            "token_calibration_version",
            "token_top_contributors",
            "token_duration_ms",
            "token_warnings",
            "token_entities",
        }
        assert expected_keys <= set(payload)
        assert payload["token_calibration_version"] == "1.0"
        assert payload["token_content_multiplier"] == 0.1
        assert payload["token_element_counts"] == {
            "csm": 2,
            "cfm": 0,
            "total": 2,
            "unknown_csm": 0,
            "unknown_cfm": 0,
        }
        for entry in payload["token_top_contributors"]:
            assert set(entry) == {"type", "count", "total", "content_tokens"}
        assert len(payload["token_entities"]) == 2
        for entity in payload["token_entities"]:
            assert set(entity) == {
                "element_id",
                "element_type",
                "element_name",
                "model_source",
                "applied_weight",
                "content_token_count",
                "content_score",
                "partial_score",
                "evidence_ref",
            }

    def test_handle_emits_token_points_event(self):
        from dataclasses import replace

        from specmetrics.kernel.events import EventType, PipelineEvent
        from specmetrics.kernel.pipeline_context import PipelineContext
        from specmetrics.plugins.measurement.token_points.plugin import (
            TokenPointsHandler,
        )

        handler = TokenPointsHandler()
        ev = _make_csm_evidence()
        csm = CanonicalSpecificationModel(
            run_id="csm-event",
            decisions={
                _uid(): Decision(
                    id=_uid(),
                    description="Some decision",
                    evidence_references=[ev],
                ),
            },
            metadata=CsmBuildMetadata(run_id="csm-event", version="1.0", source="test"),
        )
        ctx = replace(
            PipelineContext(),
            canonical_spec_model=csm,
            metadata=_make_default_calibration(),
        )
        event = PipelineEvent(
            event_type=EventType.MEASUREMENT_COMPLETED,
            publisher="test",
            payload={},
            context=ctx,
        )
        result_ctx = handler.handle(event)
        published = [
            e
            for e in result_ctx.published_events
            if e.publisher == "token_points"
        ]
        assert len(published) == 1
        assert published[0].event_type == EventType.TOKEN_POINTS_MEASURED
        assert published[0].publisher == "token_points"
        assert published[0].payload == result_ctx.measurement_result


class TestPluginMetadata:
    def test_metadata_fields(self):
        from specmetrics.kernel.events import EventType
        from specmetrics.kernel.plugin_metadata import PluginType
        from specmetrics.plugins.measurement.token_points.plugin import (
            TokenPointsHandler,
            create_token_points_measurement_metadata,
        )

        metadata = create_token_points_measurement_metadata()
        assert metadata.id == "token_points"
        assert metadata.api_version == "0.1.0"
        assert metadata.version == "0.1.0"
        assert metadata.plugin_type == PluginType.MEASUREMENT
        assert metadata.name == "Token Points"
        assert metadata.description == (
            "Token Points measurement \u2014 estimates AI computational cost "
            "from CFM and CSM with per-element explainability"
        )
        assert metadata.handled_event_types == (EventType.MEASUREMENT_COMPLETED,)
        assert callable(metadata.handler_factory)
        assert isinstance(metadata.handler_factory(), TokenPointsHandler)
