from __future__ import annotations

import uuid

from specmetrics.kernel.cfm.model import (
    BuildMetadata as CfmBuildMetadata,
)
from specmetrics.kernel.cfm.model import (
    BusinessRule,
    CanonicalFunctionalModel,
    FunctionalProcess,
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
    Reference,
)
from specmetrics.kernel.csm.model import (
    EvidenceRef as CsmEvidenceRef,
)
from specmetrics.plugins.measurement.cognitive_points.calculator import (
    calculate,
)
from specmetrics.plugins.measurement.cognitive_points.calibration import (
    CognitiveCalibrationProfile,
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


def _make_default_calibration() -> CognitiveCalibrationProfile:
    return CognitiveCalibrationProfile()


class TestContentBasedScoring:
    def test_longer_description_scores_higher(self):
        cal = _make_default_calibration()
        ev = _make_cfm_evidence()

        short_cfm = CanonicalFunctionalModel(
            run_id="cfm-short",
            functional_processes={
                _uid(): FunctionalProcess(
                    id=_uid(),
                    name="Short",
                    description="word",
                    actor_ids=[],
                    operation_ids=[],
                    evidence=ev,
                ),
            },
            metadata=CfmBuildMetadata(run_id="cfm-short", version="1.0", source="test"),
        )
        long_cfm = CanonicalFunctionalModel(
            run_id="cfm-long",
            functional_processes={
                _uid(): FunctionalProcess(
                    id=_uid(),
                    name="Long",
                    description="word " * 1000,
                    actor_ids=[],
                    operation_ids=[],
                    evidence=ev,
                ),
            },
            metadata=CfmBuildMetadata(run_id="cfm-long", version="1.0", source="test"),
        )

        short_result = calculate(short_cfm, None, cal, run_id="test-short")
        long_result = calculate(long_cfm, None, cal, run_id="test-long")
        assert long_result.raw_score > short_result.raw_score

    def test_content_token_count_populated(self):
        cal = _make_default_calibration()
        ev = _make_csm_evidence()
        csm = CanonicalSpecificationModel(
            run_id="csm-content",
            decisions={
                _uid(): Decision(
                    id=_uid(),
                    description="A decision with some text",
                    evidence_references=[ev],
                ),
            },
            metadata=CsmBuildMetadata(
                run_id="csm-content", version="1.0", source="test"
            ),
        )
        result = calculate(None, csm, cal, run_id="test-ctc")
        for contrib in result.specification_review_effort.contributions:
            assert contrib.content_token_count > 0
            assert contrib.content_score > 0.0
            assert (
                abs(
                    contrib.partial_score
                    - (contrib.cognitive_weight + contrib.content_score)
                )
                < 0.001
            )

    def test_empty_content_gets_zero_content_score(self):
        cal = _make_default_calibration()
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
        result = calculate(cfm, None, cal, run_id="test-empty")
        for contrib in result.functional_validation_effort.contributions:
            assert contrib.content_token_count == 0
            assert contrib.content_score == 0.0
            assert contrib.partial_score == contrib.cognitive_weight

    def test_content_multiplier_zero_disables_content(self):
        ev = _make_cfm_evidence()
        cfm = CanonicalFunctionalModel(
            run_id="cfm-zero",
            functional_processes={
                _uid(): FunctionalProcess(
                    id=_uid(),
                    name="Test",
                    description="A long description",
                    actor_ids=[],
                    operation_ids=[],
                    evidence=ev,
                ),
            },
            metadata=CfmBuildMetadata(run_id="cfm-zero", version="1.0", source="test"),
        )
        cal = CognitiveCalibrationProfile(content_multiplier=0.0)
        result = calculate(cfm, None, cal, run_id="test-zero")
        for contrib in result.functional_validation_effort.contributions:
            assert contrib.content_score == 0.0
            assert contrib.partial_score == contrib.cognitive_weight


class TestCrossSpecComparability:
    def test_3x_content_volume_ratio_ge_1_5x(self):
        cal = _make_default_calibration()
        ev = _make_cfm_evidence()
        short_text = "word " * 50
        long_text = "word " * 150

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
        ratio = large_result.raw_score / small_result.raw_score
        assert ratio >= 1.5, (
            f"Expected ratio >= 1.5 for ~3x content volume, got {ratio:.2f}"
        )


class TestSubTypeClassification:
    def test_business_rule_derivation_is_analyze_or_higher(self):
        cal = _make_default_calibration()
        ev = _make_cfm_evidence()
        cfm = CanonicalFunctionalModel(
            run_id="cfm-br-derivation",
            business_rules={
                _uid(): BusinessRule(
                    id=_uid(),
                    name="Derivation Rule",
                    description="Computes total from inputs",
                    rule_type="derivation",
                    evidence=ev,
                ),
            },
            metadata=CfmBuildMetadata(
                run_id="cfm-br-derivation", version="1.0", source="test"
            ),
        )
        result = calculate(cfm, None, cal, run_id="test-derivation")
        for contrib in result.functional_validation_effort.contributions:
            bloom_weight = contrib.cognitive_weight
            assert bloom_weight >= 4.0, (
                f"Expected derivation >= analyze (4.0), got {bloom_weight}"
            )

    def test_business_rule_constraint_is_apply(self):
        cal = _make_default_calibration()
        ev = _make_cfm_evidence()
        cfm = CanonicalFunctionalModel(
            run_id="cfm-br-constraint",
            business_rules={
                _uid(): BusinessRule(
                    id=_uid(),
                    name="Constraint Rule",
                    description="Must be unique",
                    rule_type="constraint",
                    evidence=ev,
                ),
            },
            metadata=CfmBuildMetadata(
                run_id="cfm-br-constraint", version="1.0", source="test"
            ),
        )
        result = calculate(cfm, None, cal, run_id="test-constraint")
        for contrib in result.functional_validation_effort.contributions:
            assert contrib.bloom_level == "apply", (
                f"Expected constraint -> apply, got {contrib.bloom_level}"
            )
            assert contrib.cognitive_weight == 3.0

    def test_unknown_element_type_defaults_to_understand(self):
        from specmetrics.plugins.measurement.cognitive_points.bloom_classifier import (
            DefaultBloomClassifier,
        )

        classifier = DefaultBloomClassifier()
        assert classifier.classify("nonexistent_type") == "understand"
        assert classifier.get_weight("understand") == 2.0

    def test_subtype_not_in_mappings_falls_back_to_base(self):
        from specmetrics.plugins.measurement.cognitive_points.bloom_classifier import (
            DefaultBloomClassifier,
        )

        classifier = DefaultBloomClassifier()
        result = classifier.classify("business_rule", None)
        assert result == "apply"


class TestPayloadExtensions:
    def test_payload_contains_new_keys(self):
        from dataclasses import replace

        from specmetrics.kernel.events import EventType, PipelineEvent
        from specmetrics.kernel.pipeline_context import PipelineContext
        from specmetrics.plugins.measurement.cognitive_points.plugin import (
            CognitivePointsHandler,
        )

        handler = CognitivePointsHandler()
        ev = _make_csm_evidence()
        csm = CanonicalSpecificationModel(
            run_id="csm-payload",
            decisions={
                _uid(): Decision(
                    id=_uid(),
                    description="Some content",
                    evidence_references=[ev],
                ),
            },
            metadata=CsmBuildMetadata(
                run_id="csm-payload", version="1.0", source="test"
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
        result_ctx = handler.handle(event)
        payload = result_ctx.measurement_result
        assert payload is not None
        assert "cognitive_content_multiplier" in payload
        assert "cognitive_content_tokens" in payload
        assert payload["cognitive_content_multiplier"] == 0.1

    def test_content_tokens_in_element_counts(self):
        from dataclasses import replace

        from specmetrics.kernel.events import EventType, PipelineEvent
        from specmetrics.kernel.pipeline_context import PipelineContext
        from specmetrics.plugins.measurement.cognitive_points.plugin import (
            CognitivePointsHandler,
        )

        handler = CognitivePointsHandler()
        ev = _make_csm_evidence()
        csm = CanonicalSpecificationModel(
            run_id="csm-ect",
            decisions={
                _uid(): Decision(
                    id=_uid(),
                    description="Decision",
                    evidence_references=[ev],
                ),
            },
            metadata=CsmBuildMetadata(run_id="csm-ect", version="1.0", source="test"),
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
        assert "cognitive_content_tokens" in payload
        assert isinstance(payload["cognitive_content_tokens"], dict)


class TestBackwardCompatibility:
    def test_content_multiplier_zero_makes_scores_uniform(self):
        ev = _make_cfm_evidence()
        cfm = CanonicalFunctionalModel(
            run_id="cfm-uniform",
            functional_processes={
                _uid(): FunctionalProcess(
                    id=_uid(),
                    name="Process A",
                    description="Long description that adds variance",
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
        cal = CognitiveCalibrationProfile(content_multiplier=0.0)
        result = calculate(cfm, None, cal, run_id="test-uniform")
        scores = {
            c.element_name: c.partial_score
            for c in result.functional_validation_effort.contributions
        }
        assert len(set(scores.values())) == 1, (
            "All same-type elements should have identical scores with content_multiplier=0"
        )

    def test_csm_references_contribute_score(self):
        cal = _make_default_calibration()
        ev = _make_csm_evidence()
        csm = CanonicalSpecificationModel(
            run_id="csm-refs",
            references={
                _uid(): Reference(
                    id=_uid(),
                    description="RFC-1234: API Spec",
                    evidence_references=[ev],
                ),
            },
            metadata=CsmBuildMetadata(run_id="csm-refs", version="1.0", source="test"),
        )
        result = calculate(None, csm, cal, run_id="test-refs")
        ref_contribs = [
            c
            for c in result.specification_review_effort.contributions
            if c.element_type == "references"
        ]
        assert len(ref_contribs) == 1
        assert ref_contribs[0].partial_score > 0

    def test_code_blocks_tokenized_as_text(self):
        cal = _make_default_calibration()
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
        result = calculate(cfm, None, cal, run_id="test-code")
        assert result.raw_score > 0
        for contrib in result.functional_validation_effort.contributions:
            assert contrib.content_token_count > 0
