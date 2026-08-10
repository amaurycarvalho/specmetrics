from __future__ import annotations

import time
import uuid

import pytest

from specmetrics.kernel.cfm.model import (
    Actor,
    BusinessRule,
    CanonicalFunctionalModel,
    DataGroup,
    FunctionalProcess,
    Operation,
    Relationship,
)
from specmetrics.kernel.cfm.model import (
    BuildMetadata as CfmBuildMetadata,
)
from specmetrics.kernel.cfm.model import (
    EvidenceRef as CfmEvidenceRef,
)
from specmetrics.kernel.csm.model import (
    AcceptanceCriterion,
    Assumption,
    CanonicalSpecificationModel,
    Constraint,
    Decision,
    GlossaryTerm,
    OpenQuestion,
    Risk,
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
from specmetrics.plugins.measurement.token_points.calculator import calculate
from specmetrics.plugins.measurement.token_points.models import TokenPointsMeasurement


def _uid() -> str:
    return str(uuid.uuid4())


def _make_default_calibration() -> CalibrationProfile:
    return CalibrationProfile(
        version="1.0",
        specification_cost=SpecificationCostWeights(),
        code_generation_cost=CodeGenerationCostWeights(),
    )


def _make_cfm_evidence() -> CfmEvidenceRef:
    return CfmEvidenceRef(
        graph_node_id="gn-cfm-001", document_id="doc-001", text="cfm evidence"
    )


def _make_csm_evidence() -> CsmEvidenceRef:
    return CsmEvidenceRef(
        graph_node_id="gn-csm-001", document_id="doc-001", text="csm evidence"
    )


def _make_cfm() -> CanonicalFunctionalModel:
    ev = _make_cfm_evidence()
    return CanonicalFunctionalModel(
        run_id="cfm-test-001",
        actors={
            _uid(): Actor(id=_uid(), name="User", actor_type="person", evidence=ev),
        },
        functional_processes={
            _uid(): FunctionalProcess(
                id=_uid(),
                name="Login",
                description="User login",
                actor_ids=[],
                operation_ids=[],
                evidence=ev,
            ),
        },
        business_rules={
            _uid(): BusinessRule(
                id=_uid(),
                name="Password Policy",
                description="Min 8 chars",
                evidence=ev,
            ),
        },
        data_groups={
            _uid(): DataGroup(id=_uid(), name="User Data", evidence=ev),
        },
        relationships=[
            Relationship(
                id=_uid(),
                source_id=_uid(),
                target_id=_uid(),
                relationship_type="triggers",
                evidence=ev,
            ),
        ],
        operations={
            _uid(): Operation(
                id=_uid(),
                name="Authenticate",
                parent_process_id=_uid(),
                evidence=ev,
            ),
        },
        metadata=CfmBuildMetadata(run_id="cfm-test-001", version="1.0", source="test"),
    )


def _make_csm() -> CanonicalSpecificationModel:
    ev = _make_csm_evidence()
    return CanonicalSpecificationModel(
        run_id="csm-test-001",
        specification_activities={
            _uid(): SpecificationActivity(
                id=_uid(),
                description="Initial exploration",
                activity_type="exploration",
                evidence_references=[ev],
            ),
            _uid(): SpecificationActivity(
                id=_uid(),
                description="Requirements clarification",
                activity_type="clarification",
                evidence_references=[ev],
            ),
        },
        decisions={
            _uid(): Decision(
                id=_uid(),
                description="Use PostgreSQL",
                evidence_references=[ev],
            ),
        },
        assumptions={
            _uid(): Assumption(
                id=_uid(),
                description="Users have internet",
                evidence_references=[ev],
            ),
        },
        constraints={
            _uid(): Constraint(
                id=_uid(),
                description="GDPR compliance",
                constraint_type="regulatory",
                evidence_references=[ev],
            ),
        },
        risks={
            _uid(): Risk(
                id=_uid(), description="Performance risk", evidence_references=[ev]
            ),
        },
        open_questions={
            _uid(): OpenQuestion(
                id=_uid(), description="Scaling strategy", evidence_references=[ev]
            ),
        },
        acceptance_criteria={
            _uid(): AcceptanceCriterion(
                id=_uid(),
                description="Login works",
                verification_method="test",
                evidence_references=[ev],
            ),
        },
        glossary_terms={
            _uid(): GlossaryTerm(
                id=_uid(),
                description="SLA definition",
                evidence_references=[ev],
            ),
        },
        metadata=CsmBuildMetadata(run_id="csm-test-001", version="1.0", source="test"),
    )


class TestCalculateFromKnownModels:
    def test_calculate_from_known_models(self):
        cfm = _make_cfm()
        csm = _make_csm()
        calibration = _make_default_calibration()
        result = calculate(cfm, csm, calibration, run_id="test-run-001")
        assert isinstance(result, TokenPointsMeasurement)
        assert result.run_id == "test-run-001"
        assert result.total_score > 0
        assert result.specification_cost.total > 0
        assert result.code_generation_cost.total > 0
        assert len(result.specification_cost.contributions) > 0
        assert len(result.code_generation_cost.contributions) > 0

    def test_deterministic(self):
        cfm = _make_cfm()
        csm = _make_csm()
        calibration = _make_default_calibration()
        result1 = calculate(cfm, csm, calibration, run_id="det-test")
        result2 = calculate(cfm, csm, calibration, run_id="det-test")
        d1 = result1.model_dump()
        d2 = result2.model_dump()
        d1.pop("measured_at", None)
        d2.pop("measured_at", None)
        d1["measurement_metadata"]["duration_ms"] = 0
        d2["measurement_metadata"]["duration_ms"] = 0
        assert d1 == d2

    def test_missing_csm(self):
        cfm = _make_cfm()
        calibration = _make_default_calibration()
        result = calculate(cfm, None, calibration, run_id="no-csm")
        assert result.specification_cost.total == 0.0
        assert result.code_generation_cost.total > 0
        warning_codes = [w.code for w in result.measurement_metadata.warnings]
        assert "MISSING_CSM" in warning_codes

    def test_missing_cfm(self):
        csm = _make_csm()
        calibration = _make_default_calibration()
        result = calculate(None, csm, calibration, run_id="no-cfm")
        assert result.code_generation_cost.total == 0.0
        assert result.specification_cost.total > 0
        warning_codes = [w.code for w in result.measurement_metadata.warnings]
        assert "MISSING_CFM" in warning_codes

    def test_both_missing(self):
        calibration = _make_default_calibration()
        result = calculate(None, None, calibration, run_id="empty")
        assert result.total_score == 0.0
        assert result.specification_cost.total == 0.0
        assert result.code_generation_cost.total == 0.0

    def test_metadata_tracks_counts(self):
        cfm = _make_cfm()
        csm = _make_csm()
        result = calculate(cfm, csm, _make_default_calibration(), run_id="meta")
        assert result.measurement_metadata.total_elements_processed > 0
        assert result.measurement_metadata.csm_element_count > 0
        assert result.measurement_metadata.cfm_element_count > 0
        assert result.measurement_metadata.total_elements_processed == (
            result.measurement_metadata.csm_element_count
            + result.measurement_metadata.cfm_element_count
        )


class TestCalibrationWeights:
    def test_custom_weights_affect_result(self):
        cfm = _make_cfm()
        csm = _make_csm()
        default_cal = _make_default_calibration()
        custom_cal = CalibrationProfile(
            version="1.0",
            specification_cost=SpecificationCostWeights(
                decisions=10.0,
                assumptions=10.0,
            ),
            code_generation_cost=CodeGenerationCostWeights(
                functional_processes=20.0,
            ),
        )
        default_result = calculate(cfm, csm, default_cal, run_id="default")
        custom_result = calculate(cfm, csm, custom_cal, run_id="custom")
        assert custom_result.total_score > default_result.total_score


class TestContributionDefaults:
    def test_empty_content_is_zero(self):
        cfm = _make_cfm()
        csm = _make_csm()
        result = calculate(cfm, csm, _make_default_calibration(), run_id="empty-content")
        for contrib in result.specification_cost.contributions + result.code_generation_cost.contributions:
            assert contrib.content_token_count == 0 or contrib.content_score >= 0
        assert all(isinstance(c.partial_score, float) for c in result.specification_cost.contributions)

    def test_counts_are_accurate(self):
        cfm = _make_cfm()
        csm = _make_csm()
        result = calculate(cfm, csm, _make_default_calibration(), run_id="counts")
        assert result.measurement_metadata.csm_element_count > 0
        assert result.measurement_metadata.cfm_element_count > 0
        assert result.measurement_metadata.unknown_csm_element_count == 0
        assert result.measurement_metadata.unknown_cfm_element_count == 0

    def test_unknown_cfm_elements_are_warned(self):
        from specmetrics.kernel.cfm.model import (
            CanonicalFunctionalModel,
            UnclassifiedElement,
        )
        ev = CfmEvidenceRef(
            graph_node_id="gn-unk", document_id="doc-unk", text="unk"
        )
        unclassified = {
            _uid(): UnclassifiedElement(
                id=_uid(), original_type="x", content="c", evidence=ev
            )
            for _ in range(2)
        }
        cfm = CanonicalFunctionalModel(
            run_id="unk",
            unclassified=unclassified,
            metadata=CfmBuildMetadata(run_id="unk", version="1.0", source="test"),
        )
        csm = _make_csm()
        result = calculate(cfm, csm, _make_default_calibration(), run_id="unk")
        codes = [w.code for w in result.measurement_metadata.warnings]
        assert "UNKNOWN_CFM_ELEMENTS" in codes
        assert result.measurement_metadata.unknown_cfm_element_count == 2

    def test_reference_element_uses_description(self):
        from specmetrics.kernel.csm.model import CanonicalSpecificationModel, Reference
        ev = CsmEvidenceRef(
            graph_node_id="gn-ref", document_id="doc-ref", text="t"
        )
        csm = CanonicalSpecificationModel(
            run_id="ref-csm",
            references={
                _uid(): Reference(
                    id=_uid(),
                    description="Some reference",
                    evidence_references=[ev],
                ),
            },
            metadata=CsmBuildMetadata(run_id="ref-csm", version="1.0", source="test"),
        )
        result = calculate(None, csm, _make_default_calibration(), run_id="ref")
        contrib = next(
            c
            for c in result.specification_cost.contributions
            if c.element_type == "references"
        )
        assert contrib.element_name == next(iter(csm.references.keys()))
        assert contrib.element_type == "references"
        assert contrib.model_source == "csm"

    def test_specification_activity_contribution(self):
        csm = _make_csm()
        result = calculate(None, csm, _make_default_calibration(), run_id="acts")
        activity = next(
            c
            for c in result.specification_cost.contributions
            if c.element_type == "exploration"
        )
        assert activity.model_source == "csm"
        assert activity.element_type == "exploration"


class TestAggregation:
    def test_aggregate_summing(self):
        from specmetrics.plugins.measurement.token_points.models import (
            aggregate,
        )

        cal = _make_default_calibration()
        cfm = _make_cfm()
        csm = _make_csm()
        m1 = calculate(cfm, csm, cal, run_id="m1")
        m2 = calculate(cfm, csm, cal, run_id="m2")
        aggregated = aggregate([m1, m2])
        assert aggregated.total_score == m1.total_score + m2.total_score
        assert aggregated.specification_cost.total == (
            m1.specification_cost.total + m2.specification_cost.total
        )
        assert aggregated.code_generation_cost.total == (
            m1.code_generation_cost.total + m2.code_generation_cost.total
        )


class TestPerformance:
    @pytest.mark.slow
    def test_performance_500_elements(self):
        ev = _make_cfm_evidence()
        ops = {}
        for i in range(250):
            uid = _uid()
            ops[uid] = Operation(
                id=uid,
                name=f"Process {i}",
                parent_process_id=_uid(),
                evidence=ev,
            )
        cfm = CanonicalFunctionalModel(
            run_id="perf-test",
            operations=ops,
            metadata=CfmBuildMetadata(run_id="perf-test", version="1.0", source="test"),
        )
        csm_ev = _make_csm_evidence()
        decisions = {}
        for i in range(250):
            uid = _uid()
            decisions[uid] = Decision(
                id=uid,
                description=f"Decision {i}",
                evidence_references=[csm_ev],
            )
        csm = CanonicalSpecificationModel(
            run_id="perf-test-csm",
            decisions=decisions,
            metadata=CsmBuildMetadata(
                run_id="perf-test-csm", version="1.0", source="test"
            ),
        )
        start = time.monotonic()
        calculate(cfm, csm, _make_default_calibration(), run_id="perf")
        elapsed = time.monotonic() - start
        assert elapsed < 2.0


class TestExactCounts:
    def test_exact_element_counts(self):
        cfm = _make_cfm()
        csm = _make_csm()
        result = calculate(cfm, csm, _make_default_calibration(), run_id="counts")
        assert result.measurement_metadata.csm_element_count == 9
        assert result.measurement_metadata.cfm_element_count == 6
        assert result.measurement_metadata.total_elements_processed == 15

    def test_missing_models_zero_counts(self):
        result = calculate(None, None, _make_default_calibration(), run_id="empty")
        assert result.measurement_metadata.csm_element_count == 0
        assert result.measurement_metadata.cfm_element_count == 0
        assert result.measurement_metadata.total_elements_processed == 0


class TestWarningMessages:
    def test_missing_csm_message(self):
        cfm = _make_cfm()
        result = calculate(cfm, None, _make_default_calibration(), run_id="wmsg")
        warn = next(
            w
            for w in result.measurement_metadata.warnings
            if w.code == "MISSING_CSM"
        )
        assert warn.message == (
            "Canonical Specification Model (CSM) is not available. "
            "Specification Cost defaults to 0."
        )

    def test_missing_cfm_message(self):
        csm = _make_csm()
        result = calculate(None, csm, _make_default_calibration(), run_id="wmsg")
        warn = next(
            w
            for w in result.measurement_metadata.warnings
            if w.code == "MISSING_CFM"
        )
        assert warn.message == (
            "Canonical Functional Model (CFM) is not available. "
            "Code Generation Cost defaults to 0."
        )

    def test_unknown_cfm_warning_exact(self):
        from specmetrics.kernel.cfm.model import UnclassifiedElement

        ev = CfmEvidenceRef(
            graph_node_id="gn-unk", document_id="doc-unk", text="unk"
        )
        unclassified = {
            _uid(): UnclassifiedElement(
                id=_uid(), original_type="x", content="c", evidence=ev
            )
            for _ in range(2)
        }
        cfm = CanonicalFunctionalModel(
            run_id="unk",
            unclassified=unclassified,
            metadata=CfmBuildMetadata(run_id="unk", version="1.0", source="test"),
        )
        csm = _make_csm()
        result = calculate(cfm, csm, _make_default_calibration(), run_id="unk")
        warn = next(
            w
            for w in result.measurement_metadata.warnings
            if w.code == "UNKNOWN_CFM_ELEMENTS"
        )
        assert warn.message == (
            "2 CFM unclassified element(s) found with no configurable weight "
            "\u2014 excluded from Code Generation Cost"
        )
        assert warn.details == {"count": "2", "category": "unclassified"}


class TestElementNameTruncation:
    def test_csm_description_truncated_to_80(self):
        text = "y" * 200
        ev = _make_csm_evidence()
        csm = CanonicalSpecificationModel(
            run_id="trunc",
            specification_activities={
                _uid(): SpecificationActivity(
                    id=_uid(),
                    description=text,
                    activity_type="exploration",
                    evidence_references=[ev],
                ),
            },
            decisions={
                _uid(): Decision(
                    id=_uid(), description=text, evidence_references=[ev]
                ),
            },
            metadata=CsmBuildMetadata(run_id="trunc", version="1.0", source="test"),
        )
        result = calculate(None, csm, _make_default_calibration(), run_id="trunc")
        by_type = {
            c.element_type: c
            for c in result.specification_cost.contributions
        }
        assert by_type["exploration"].element_name == text[:80]
        assert by_type["decisions"].element_name == text[:80]

    def test_cfm_element_name_truncated_to_80(self):
        ev = _make_cfm_evidence()
        cfm = CanonicalFunctionalModel(
            run_id="trunc-cfm",
            functional_processes={
                _uid(): FunctionalProcess(
                    id=_uid(),
                    name="n" * 200,
                    description="",
                    actor_ids=[],
                    operation_ids=[],
                    evidence=ev,
                ),
            },
            metadata=CfmBuildMetadata(
                run_id="trunc-cfm", version="1.0", source="test"
            ),
        )
        result = calculate(cfm, None, _make_default_calibration(), run_id="tc")
        contrib = next(
            iter(result.code_generation_cost.contributions)
        )
        assert contrib.element_name == "n" * 80


class TestContributionFieldDetails:
    def test_evidence_ref_populated(self):
        cfm = _make_cfm()
        csm = _make_csm()
        result = calculate(cfm, csm, _make_default_calibration(), run_id="evm")
        csm_contrib = next(
            c
            for c in result.specification_cost.contributions
            if c.element_type == "exploration"
        )
        assert csm_contrib.evidence_ref is not None
        assert csm_contrib.evidence_ref.graph_node_id == "gn-csm-001"
        assert csm_contrib.evidence_ref.document_id == "doc-001"
        assert csm_contrib.evidence_ref.text == "csm evidence"
        cfm_contrib = next(
            c
            for c in result.code_generation_cost.contributions
            if c.element_type == "actors"
        )
        assert cfm_contrib.evidence_ref is not None
        assert cfm_contrib.evidence_ref.graph_node_id == "gn-cfm-001"
        assert cfm_contrib.evidence_ref.document_id == "doc-001"

    def test_element_without_evidence_reference(self):
        csm = CanonicalSpecificationModel(
            run_id="noev",
            decisions={
                _uid(): Decision(
                    id=_uid(), description="no ev", evidence_references=[]
                ),
            },
            metadata=CsmBuildMetadata(
                run_id="noev", version="1.0", source="test"
            ),
        )
        result = calculate(None, csm, _make_default_calibration(), run_id="noev")
        contrib = next(iter(result.specification_cost.contributions))
        assert contrib.evidence_ref is None

    def test_cfm_element_name_from_name(self):
        ev = _make_cfm_evidence()
        cfm = CanonicalFunctionalModel(
            run_id="name-cfm",
            functional_processes={
                _uid(): FunctionalProcess(
                    id=_uid(),
                    name="Unique Process Name",
                    description="Fallback description",
                    actor_ids=[],
                    operation_ids=[],
                    evidence=ev,
                ),
            },
            metadata=CfmBuildMetadata(
                run_id="name-cfm", version="1.0", source="test"
            ),
        )
        result = calculate(cfm, None, _make_default_calibration(), run_id="name")
        contrib = next(iter(result.code_generation_cost.contributions))
        assert contrib.element_name == "Unique Process Name"

    def test_relationship_id_is_element_id(self):
        rel_id = _uid()
        ev = _make_cfm_evidence()
        cfm = CanonicalFunctionalModel(
            run_id="rel",
            relationships=[
                Relationship(
                    id=rel_id,
                    source_id=_uid(),
                    target_id=_uid(),
                    relationship_type="triggers",
                    evidence=ev,
                )
            ],
            metadata=CfmBuildMetadata(run_id="rel", version="1.0", source="test"),
        )
        result = calculate(cfm, None, _make_default_calibration(), run_id="rel")
        contrib = next(
            c
            for c in result.code_generation_cost.contributions
            if c.element_type == "relationships"
        )
        assert contrib.element_id == rel_id

    def test_cfm_content_combines_name_and_description(self):
        from specmetrics.kernel.token_utils import count_tokens

        ev = _make_cfm_evidence()
        cfm = CanonicalFunctionalModel(
            run_id="content-cfm",
            functional_processes={
                _uid(): FunctionalProcess(
                    id=_uid(),
                    name="abc",
                    description="def ghi",
                    actor_ids=[],
                    operation_ids=[],
                    evidence=ev,
                ),
            },
            metadata=CfmBuildMetadata(
                run_id="content-cfm", version="1.0", source="test"
            ),
        )
        result = calculate(cfm, None, _make_default_calibration(), run_id="cc")
        contrib = next(iter(result.code_generation_cost.contributions))
        assert contrib.content_token_count > 0
        assert contrib.content_token_count == count_tokens("abc def ghi")


def test_extract_content_text_csm_combines():
    """Kills _extract_content_text_csm getattr and string-join mutants."""
    from specmetrics.plugins.measurement.token_points.calculator import (
        _extract_content_text_csm,
    )

    class _E:
        name = "Alpha"
        description = "Beta"

    assert _extract_content_text_csm(_E()) == "Alpha Beta"


def test_extract_content_text_csm_empty():
    """Kills _extract_content_text_csm default fallback mutants."""
    from specmetrics.plugins.measurement.token_points.calculator import (
        _extract_content_text_csm,
    )

    class _E:
        name = None
        description = None

    assert _extract_content_text_csm(_E()) == ""


def test_extract_content_text_csm_missing_attrs():
    """Kills _extract_content_text_csm missing-attribute fallback mutants."""
    from specmetrics.plugins.measurement.token_points.calculator import (
        _extract_content_text_csm,
    )

    class _E:
        pass

    assert _extract_content_text_csm(_E()) == ""


def test_extract_content_text_cfm_relationships():
    """Kills the relationships-only branch in _extract_content_text_cfm."""
    from specmetrics.plugins.measurement.token_points.calculator import (
        _extract_content_text_cfm,
    )

    class _Rel:
        name = "Rel Name"
        description = "Desc"

    assert _extract_content_text_cfm(_Rel(), "relationships") == "Rel Name"


def test_extract_content_text_cfm_other():
    """Kills the combined branch in _extract_content_text_cfm."""
    from specmetrics.plugins.measurement.token_points.calculator import (
        _extract_content_text_cfm,
    )

    class _Op:
        name = "Op"
        description = "Desc"

    assert _extract_content_text_cfm(_Op(), "operations") == "Op Desc"


def test_build_token_contribution_empty_content():
    """Kills the empty-content branch and log event of _build_token_contribution."""
    from specmetrics.plugins.measurement.token_points.calculator import (
        _build_token_contribution,
    )

    c = _build_token_contribution(
        element_id="e1",
        element_type="operation",
        element_name="Op",
        model_source="cfm",
        applied_weight=1.0,
        content_text="",
        content_multiplier=2.0,
        evidence_ref=None,
    )
    assert c.content_token_count == 0
    assert c.content_score == 0.0
    assert c.partial_score == 1.0
    assert c.evidence_ref is None


def test_build_token_contribution_content():
    """Kills the count/content-score and field-assignment mutants."""
    from specmetrics.plugins.measurement.token_points.calculator import (
        _build_token_contribution,
    )

    c = _build_token_contribution(
        element_id="e2",
        element_type="data_group",
        element_name="DG",
        model_source="cfm",
        applied_weight=3.0,
        content_text="hello world",
        content_multiplier=0.5,
        evidence_ref=None,
    )
    assert c.element_id == "e2"
    assert c.element_type == "data_group"
    assert c.content_token_count == 2
    assert c.content_score == 1.0
    assert c.partial_score == 4.0


def test_collect_csm_none_warns():
    """Kills the MISSING_CSM warning and zero-count mutants in _collect_csm."""
    from specmetrics.plugins.measurement.token_points.calculator import (
        _collect_csm,
    )
    from specmetrics.plugins.measurement.token_points.models import MeasurementWarning

    warnings: list[MeasurementWarning] = []
    contribs, count, unknown = _collect_csm(None, object(), 1.0, warnings)
    assert contribs == []
    assert count == 0
    assert unknown == 0
    assert len(warnings) == 1
    assert warnings[0].code == "MISSING_CSM"


def test_collect_cfm_none_warns():
    """Kills the MISSING_CFM warning and zero-count mutants in _collect_cfm."""
    from specmetrics.plugins.measurement.token_points.calculator import (
        _collect_cfm,
    )
    from specmetrics.plugins.measurement.token_points.models import MeasurementWarning

    warnings: list[MeasurementWarning] = []
    contribs, count, unknown = _collect_cfm(None, object(), 1.0, warnings)
    assert contribs == []
    assert count == 0
    assert unknown == 0
    assert len(warnings) == 1
    assert warnings[0].code == "MISSING_CFM"


def test_collection_items_variants():
    """Kills _collection_items dict/list/empty branch mutants."""
    from specmetrics.plugins.measurement.token_points.calculator import (
        _collection_items,
    )

    assert _collection_items({"a": 1}) == [("a", 1)]
    assert _collection_items([1, 2]) == [("0", 1), ("1", 2)]
    assert _collection_items(None) == []


def test_csm_evidence_none():
    """Kills the empty-evidence early return in _csm_evidence."""
    from specmetrics.plugins.measurement.token_points.calculator import _csm_evidence

    assert _csm_evidence([]) is None
    assert _csm_evidence(None) is None


def test_cfm_evidence_none():
    """Kills the None-evidence early return in _cfm_evidence."""
    from specmetrics.plugins.measurement.token_points.calculator import _cfm_evidence

    assert _cfm_evidence(None) is None
