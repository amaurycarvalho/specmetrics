from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from structlog.testing import capture_logs

from specmetrics.kernel.cfm.metadata import BuildMetadata as CfmMetadata
from specmetrics.kernel.cfm.model import (
    CanonicalFunctionalModel,
    FunctionalProcess,
)
from specmetrics.kernel.cfm.model import (
    EvidenceRef as CfmEvidenceRef,
)
from specmetrics.kernel.csm.metadata import BuildMetadata as CsmMetadata
from specmetrics.kernel.csm.model import (
    CanonicalSpecificationModel,
    Decision,
    Reference,
    SpecificationActivity,
)
from specmetrics.kernel.csm.model import (
    EvidenceRef as CsmEvidenceRef,
)
from specmetrics.kernel.token_utils import count_tokens
from specmetrics.plugins.measurement.cognitive_points._contribution import (
    build_contribution,
)
from specmetrics.plugins.measurement.cognitive_points._processors import (
    iter_cfm_collection_items,
    process_cfm,
    process_csm,
)
from specmetrics.plugins.measurement.cognitive_points.bloom_classifier import (
    DefaultBloomClassifier,
)
from specmetrics.plugins.measurement.cognitive_points.models import MeasurementWarning

IDS = {
    "activity": "fa5f5de4-1240-41f8-93ad-3d0d81d183af",
    "decision": "4eb2da3b-56ea-4673-a124-3682e8462f51",
}


def _csm() -> CanonicalSpecificationModel:
    metadata = CsmMetadata(run_id="test-csm", created_at=datetime.now(UTC))
    return CanonicalSpecificationModel(
        run_id="test-csm",
        specification_activities={
            IDS["activity"]: SpecificationActivity(
                id=IDS["activity"],
                description="Explore requirements",
                activity_type="exploration",
                evidence_references=[
                    CsmEvidenceRef(graph_node_id="g1", document_id="d1", text="t"),
                ],
            ),
        },
        decisions={
            IDS["decision"]: Decision(
                id=IDS["decision"],
                description="Chose the green solution",
                evidence_references=[
                    CsmEvidenceRef(graph_node_id="g2", document_id="d2", text="t2"),
                ],
            ),
        },
        references={
            IDS["activity"]: Reference(
                id=IDS["activity"],
                description="Ext link",
                evidence_references=[],
                original_label="docs",
            ),
        },
        metadata=metadata,
    )


def _cfm() -> CanonicalFunctionalModel:
    metadata = CfmMetadata(run_id="test-cfm", created_at=datetime.now(UTC))
    return CanonicalFunctionalModel(
        run_id="test-cfm",
        functional_processes={
            "fp-001": FunctionalProcess(
                id="fp-001",
                name="User Login",
                evidence=CfmEvidenceRef(graph_node_id="ng1", document_id="d9", text="t"),
            ),
        },
        metadata=metadata,
    )


class TestProcessCsm:
    def setup_method(self) -> None:
        self.classifier = DefaultBloomClassifier()

    def test_process_spec_activities_and_entities(self) -> None:
        csm = _csm()
        contributions = []
        bloom_counts: dict[str, int] = {}
        warnings: list[MeasurementWarning] = []
        process_csm(csm, self.classifier, contributions, bloom_counts, warnings, 0.5)

        assert len(contributions) >= 1
        activity = next(c for c in contributions if c.element_type == "exploration")
        assert activity.element_id == IDS["activity"]
        assert activity.model_source == "csm"
        assert activity.bloom_level == "understand"
        assert activity.cognitive_weight == 2.0
        assert activity.evidence_ref is not None

        decision = next(c for c in contributions if c.element_type == "decisions")
        assert decision.element_type == "decisions"
        assert decision.bloom_level == "evaluate"

    def test_reference_contributions(self) -> None:
        csm = _csm()
        contributions, bloom_counts, warnings = [], {}, []
        process_csm(csm, self.classifier, contributions, bloom_counts, warnings, 1.0)
        assert any(c.element_type == "references" for c in contributions)

    def test_empty_models_no_contributions(self) -> None:
        csm = _csm()
        csm = csm.model_copy(
            update={
                "specification_activities": {},
                "decisions": {},
                "assumptions": {},
                "constraints": {},
                "risks": {},
                "open_questions": {},
                "acceptance_criteria": {},
                "glossary_terms": {},
                "references": {},
            }
        )
        contributions, bloom_counts, warnings = [], {}, []
        process_csm(csm, self.classifier, contributions, bloom_counts, warnings, 1.0)
        assert contributions == []


class TestProcessCfm:
    def setup_method(self) -> None:
        self.classifier = DefaultBloomClassifier()

    def test_process_functional_processes(self) -> None:
        cfm = _cfm()
        contributions: list = []
        bloom_counts: dict[str, int] = {}
        warnings: list[MeasurementWarning] = []
        process_cfm(cfm, self.classifier, contributions, bloom_counts, warnings, 0.5)
        fp = next(c for c in contributions if c.element_type == "functional_processes")
        assert fp.element_id == "fp-001"
        assert fp.model_source == "cfm"
        assert fp.bloom_level == "create"
        assert fp.cognitive_weight == 8.0

    def test_unclassified_warning(self) -> None:
        cfm = _cfm()
        cfm = cfm.model_copy(update={"unclassified": {"u1": object()}})
        contributions, bloom_counts, warnings = [], {}, []
        process_cfm(cfm, self.classifier, contributions, bloom_counts, warnings, 1.0)
        unk = next(w for w in warnings if w.code == "UNKNOWN_CFM_ELEMENTS")
        assert unk.details == {"count": "1", "category": "unclassified"}


def _rich_csm() -> SimpleNamespace:
    return SimpleNamespace(
        specification_activities={
            "a1": SimpleNamespace(
                activity_type="exploration", description="explore", evidence_references=[]
            ),
            "a2": SimpleNamespace(
                activity_type="clarification", description="clarify", evidence_references=[]
            ),
        },
        decisions={
            "d1": SimpleNamespace(
                description="decide", evidence_references=[]
            ),
        },
        constraints={
            "c1": SimpleNamespace(
                description="constrain", evidence_references=[]
            ),
        },
        assumptions={},
        risks={},
        open_questions={},
        acceptance_criteria={},
        glossary_terms={},
        references={
            "r1": SimpleNamespace(
                title="Docs", url="http://example.com", evidence_references=[]
            ),
        },
    )


class TestProcessCsmDetailed:
    def setup_method(self) -> None:
        self.classifier = DefaultBloomClassifier()

    def test_rich_bloom_counts_and_names(self) -> None:
        contributions, bloom_counts, warnings = [], {}, []
        process_csm(
            _rich_csm(), self.classifier, contributions, bloom_counts, warnings, 0.5
        )
        assert bloom_counts == {
            "understand": 2,
            "analyze": 1,
            "evaluate": 1,
            "apply": 1,
        }
        by_id = {c.element_id: c for c in contributions}
        assert by_id["a2"].bloom_level == "analyze"
        assert by_id["c1"].bloom_level == "apply"
        assert by_id["a1"].element_name == "explore"

    def test_reference_content_text_and_no_evidence(self) -> None:
        from specmetrics.kernel.token_utils import count_tokens

        contributions, bloom_counts, warnings = [], {}, []
        csm = _rich_csm()
        process_csm(csm, self.classifier, contributions, bloom_counts, warnings, 0.5)
        ref = next(c for c in contributions if c.element_type == "references")
        assert ref.content_token_count == count_tokens("Docs https://example.com")
        assert ref.evidence_ref is None

    def test_spec_activity_without_description_falls_back_to_id(self) -> None:
        csm = SimpleNamespace(
            specification_activities={
                "hidden-id": SimpleNamespace(
                    activity_type="exploration", evidence_references=[]
                ),
            },
            references={},
            decisions={},
            assumptions={},
            constraints={},
            risks={},
            open_questions={},
            acceptance_criteria={},
            glossary_terms={},
        )
        contributions, bloom_counts, warnings = [], {}, []
        process_csm(csm, self.classifier, contributions, bloom_counts, warnings, 1.0)
        assert contributions[0].element_name == "hidden-id"

    def test_long_name_truncated_to_80(self) -> None:
        long_name = "x" * 100
        csm = SimpleNamespace(
            specification_activities={
                "a1": SimpleNamespace(
                    activity_type="exploration", description=long_name, evidence_references=[]
                ),
            },
            references={},
            decisions={},
            assumptions={},
            constraints={},
            risks={},
            open_questions={},
            acceptance_criteria={},
            glossary_terms={},
        )
        contributions, bloom_counts, warnings = [], {}, []
        process_csm(csm, self.classifier, contributions, bloom_counts, warnings, 1.0)
        assert contributions[0].element_name == long_name[:80]


class TestProcessCfmDetailed:
    def setup_method(self) -> None:
        self.classifier = DefaultBloomClassifier()

    def test_cfm_evidence_propagated(self) -> None:
        cfm = _cfm()
        contributions, bloom_counts, warnings = [], {}, []
        process_cfm(cfm, self.classifier, contributions, bloom_counts, warnings, 1.0)
        fp = next(c for c in contributions if c.element_type == "functional_processes")
        assert fp.evidence_ref is not None
        assert fp.evidence_ref.graph_node_id == "ng1"

    def test_no_warning_when_no_unclassified(self) -> None:
        cfm = _cfm()
        contributions, bloom_counts, warnings = [], {}, []
        process_cfm(cfm, self.classifier, contributions, bloom_counts, warnings, 1.0)
        assert all(w.code != "UNKNOWN_CFM_ELEMENTS" for w in warnings)

    def test_cfm_bloom_counts(self) -> None:
        cfm = _cfm()
        contributions, bloom_counts, warnings = [], {}, []
        process_cfm(cfm, self.classifier, contributions, bloom_counts, warnings, 1.0)
        assert bloom_counts == {"create": 1}


class TestIterCfmCollectionItems:
    def test_dict_collection(self) -> None:
        items = iter_cfm_collection_items({"a": 1, "b": 2})
        assert items == [("a", 1), ("b", 2)]

    def test_list_collection(self) -> None:
        class Obj:
            def __init__(self, iid: str) -> None:
                self.id = iid

        items = iter_cfm_collection_items([Obj("x"), Obj("y")])
        assert [i[0] for i in items] == ["x", "y"]
        assert [i[1].id for i in items] == ["x", "y"]

    def test_empty_collections(self) -> None:
        assert iter_cfm_collection_items({}) == []
        assert iter_cfm_collection_items(None) == []

    def test_list_collection_missing_id_falls_back_to_index(self) -> None:
        items = iter_cfm_collection_items([object(), object()])
        assert [i[0] for i in items] == ["0", "1"]

class _RecordingClassifier:
    """Classifier that records classify/get_weight arguments for mutation-killing tests."""

    def __init__(self) -> None:
        self.classify_calls: list[tuple[str, object]] = []
        self.weight_calls: list[str] = []

    def classify(self, elem_type: str, elem: object) -> str:
        self.classify_calls.append((elem_type, elem))
        return "understand"

    def get_weight(self, bloom_level: str) -> float:
        self.weight_calls.append(bloom_level)
        return 2.0


def _proc_csm(csm: object, classifier: object = None) -> tuple[list, dict, list]:
    contributions: list = []
    bloom_counts: dict[str, int] = {}
    warnings: list[MeasurementWarning] = []
    process_csm(csm, classifier or DefaultBloomClassifier(), contributions, bloom_counts, warnings, 1.0)
    return contributions, bloom_counts, warnings


def _entity_csm() -> SimpleNamespace:
    return SimpleNamespace(
        specification_activities={
            "act-1": SimpleNamespace(
                activity_type="exploration", description="explore", evidence_references=[]
            ),
        },
        decisions={
            "dec-1": SimpleNamespace(
                description="decide",
                name="named",
                evidence_references=[
                    SimpleNamespace(graph_node_id="g9", document_id="d9", text="t9"),
                ],
            ),
        },
        references={
            "ref-1": SimpleNamespace(
                title="Docs", url="http://example.com", evidence_references=[]
            ),
        },
        assumptions={},
        constraints={},
        risks={},
        open_questions={},
        acceptance_criteria={},
        glossary_terms={},
    )


def test_process_csm_missing_specification_activities_attr_no_crash() -> None:
    """Kills _process_csm_entities__mutmut_19/22 (getattr default for specification_activities)."""
    csm = _entity_csm()
    del csm.specification_activities
    contributions, _, _ = _proc_csm(csm)
    assert {c.element_id for c in contributions} == {"dec-1", "ref-1"}


def test_process_csm_missing_references_attr_no_crash() -> None:
    """Kills _process_csm_references__mutmut_3/6 (getattr default for references)."""
    csm = _entity_csm()
    del csm.references
    contributions, _, _ = _proc_csm(csm)
    assert {c.element_id for c in contributions} == {"act-1", "dec-1"}


def test_classifier_receives_real_elem_type_and_elem() -> None:
    """Kills _process_csm_references__mutmut_13/14/16 and _process_csm_entities__mutmut_30/32."""
    recorder = _RecordingClassifier()
    csm = _entity_csm()
    _proc_csm(csm, recorder)
    activity = csm.specification_activities["act-1"]
    ref = csm.references["ref-1"]
    decision = csm.decisions["dec-1"]
    assert ("exploration", activity) in recorder.classify_calls
    assert ("references", ref) in recorder.classify_calls
    assert ("decision", decision) in recorder.classify_calls


def test_classifier_get_weight_receives_bloom_level() -> None:
    """Kills _process_csm_references__mutmut_18 and _process_csm_entities__mutmut_34."""
    recorder = _RecordingClassifier()
    csm = _entity_csm()
    _proc_csm(csm, recorder)
    assert "understand" in recorder.weight_calls


def test_bloom_counts_accumulate_by_level() -> None:
    """Kills _process_csm_references__mutmut_20/21/25/26 and _process_csm_entities__mutmut_36/37/41/42."""
    recorder = _RecordingClassifier()
    csm = _entity_csm()
    _, bloom_counts, _ = _proc_csm(csm, recorder)
    assert bloom_counts == {"understand": 3}


def test_spec_activity_element_id_propagated() -> None:
    """Kills _process_csm_references__mutmut_77 (element_id=str(None))."""
    csm = _entity_csm()
    contributions, _, _ = _proc_csm(csm)
    act = next(c for c in contributions if c.element_type == "exploration")
    assert act.element_id == "act-1"


def test_reference_content_text_and_multiplier_propagated() -> None:
    """Kills _process_csm_references__mutmut_65/66 (content_text/content_multiplier=None)."""
    csm = _entity_csm()
    contributions, _, _ = _proc_csm(csm)
    ref = next(c for c in contributions if c.element_type == "references")
    assert ref.content_token_count == count_tokens("Docs http://example.com")
    assert ref.content_score == count_tokens("Docs http://example.com") * 1.0
    assert ref.content_token_count > 0


def test_reference_evidence_ref_built_from_evidence() -> None:
    """Kills _process_csm_references__mutmut_27/28/30/33/34/35/67/83 (evidence resolution)."""
    csm = SimpleNamespace(
        specification_activities={},
        decisions={},
        assumptions={},
        constraints={},
        risks={},
        open_questions={},
        acceptance_criteria={},
        glossary_terms={},
        references={
            "ref-2": SimpleNamespace(
                title="T",
                url="",
                evidence_references=[
                    SimpleNamespace(graph_node_id="gn-7", document_id="doc-7", text="tx"),
                ],
            ),
        },
    )
    contributions, _, _ = _proc_csm(csm)
    ref = next(c for c in contributions if c.element_type == "references")
    assert ref.element_id == "ref-2"
    assert ref.element_name == "ref-2"
    assert ref.evidence_ref is not None
    assert ref.evidence_ref.graph_node_id == "gn-7"


def test_reference_without_evidence_references_attr_no_crash() -> None:
    """Kills _process_csm_references__mutmut_33 (getattr without default raises)."""
    csm = SimpleNamespace(
        specification_activities={},
        decisions={},
        assumptions={},
        constraints={},
        risks={},
        open_questions={},
        acceptance_criteria={},
        glossary_terms={},
        references={"ref-3": SimpleNamespace(title="T", url="")},
    )
    contributions, _, _ = _proc_csm(csm)
    assert any(c.element_id == "ref-3" for c in contributions)


def test_reference_element_type_is_references() -> None:
    """Kills _process_csm_references__mutmut_9/10/11 (elem_type literal)."""
    csm = _entity_csm()
    contributions, _, _ = _proc_csm(csm)
    ref = next(c for c in contributions if c.element_type == "references")
    assert ref.element_type == "references"


def test_entity_element_id_propagated() -> None:
    """Kills _process_csm_entities__mutmut_91 (element_id=str(None))."""
    csm = _entity_csm()
    contributions, _, _ = _proc_csm(csm)
    dec = next(c for c in contributions if c.element_type == "decisions")
    assert dec.element_id == "dec-1"


def test_entity_name_prefers_description_over_name() -> None:
    """Kills _process_csm_entities__mutmut_43/45/51/52 (name resolution)."""
    csm = _entity_csm()
    contributions, _, _ = _proc_csm(csm)
    dec = next(c for c in contributions if c.element_type == "decisions")
    assert dec.element_name == "decide"


def test_entity_name_falls_back_to_name_when_no_description() -> None:
    """Kills _process_csm_entities__mutmut_46 (getattr(None,...) on description)."""
    csm = SimpleNamespace(
        specification_activities={},
        decisions={
            "dec-2": SimpleNamespace(name="only-name", evidence_references=[]),
        },
        assumptions={},
        constraints={},
        risks={},
        open_questions={},
        acceptance_criteria={},
        glossary_terms={},
        references={},
    )
    contributions, _, _ = _proc_csm(csm)
    dec = next(c for c in contributions if c.element_type == "decisions")
    assert dec.element_name == "only-name"


def test_entity_without_description_attr_falls_back_to_id() -> None:
    """Kills _process_csm_entities__mutmut_50 (getattr without default raises)."""
    csm = SimpleNamespace(
        specification_activities={},
        decisions={"dec-3": SimpleNamespace(evidence_references=[])},
        assumptions={},
        constraints={},
        risks={},
        open_questions={},
        acceptance_criteria={},
        glossary_terms={},
        references={},
    )
    contributions, _, _ = _proc_csm(csm)
    dec = next(c for c in contributions if c.element_type == "decisions")
    assert dec.element_name == "dec-3"


def test_entity_name_truncated_to_80() -> None:
    """Kills _process_csm_entities__mutmut_92/93 (element_name truncation)."""
    long_name = "x" * 81
    csm = SimpleNamespace(
        specification_activities={},
        decisions={
            "dec-4": SimpleNamespace(description=long_name, evidence_references=[]),
        },
        assumptions={},
        constraints={},
        risks={},
        open_questions={},
        acceptance_criteria={},
        glossary_terms={},
        references={},
    )
    contributions, _, _ = _proc_csm(csm)
    dec = next(c for c in contributions if c.element_type == "decisions")
    assert dec.element_name == long_name[:80]
    assert len(dec.element_name) == 80


def test_entity_evidence_ref_built_from_evidence() -> None:
    """Kills _process_csm_entities__mutmut_61/62/64/67/68/69/81/96 (evidence resolution)."""
    csm = SimpleNamespace(
        specification_activities={},
        decisions={
            "dec-5": SimpleNamespace(
                description="d",
                evidence_references=[
                    SimpleNamespace(graph_node_id="gn-5", document_id="doc-5", text="t5"),
                ],
            ),
        },
        assumptions={},
        constraints={},
        risks={},
        open_questions={},
        acceptance_criteria={},
        glossary_terms={},
        references={},
    )
    contributions, _, _ = _proc_csm(csm)
    dec = next(c for c in contributions if c.element_type == "decisions")
    assert dec.evidence_ref is not None
    assert dec.evidence_ref.graph_node_id == "gn-5"
    assert dec.evidence_ref.document_id == "doc-5"


def test_process_csm_with_non_dict_collection_is_skipped() -> None:
    """Kills _process_csm_entities__mutmut_19/22 (dict guard on entity collections)."""
    csm = SimpleNamespace(
        specification_activities={},
        decisions=[],  # list is not a dict -> skipped
        assumptions={},
        constraints={},
        risks={},
        open_questions={},
        acceptance_criteria={},
        glossary_terms={},
        references={},
    )
    contributions, _, _ = _proc_csm(csm)
    assert contributions == []


def _build_contribution(
    content_text: str = "Hello world",
    content_multiplier: float = 0.5,
    element_id: str = "e1",
    element_type: str = "decision",
    bloom_level: str = "evaluate",
    cognitive_weight: float = 2.0,
):
    return build_contribution(
        element_id=element_id,
        element_type=element_type,
        element_name="Some name",
        model_source="csm",
        bloom_level=bloom_level,
        cognitive_weight=cognitive_weight,
        content_text=content_text,
        content_multiplier=content_multiplier,
        evidence_ref=None,
    )


def test_contribution_element_id_propagated() -> None:
    """Kills build_contribution__mutmut_21/27 (element_id=None or deleted)."""
    contrib = _build_contribution(element_id="special-id")
    assert contrib.element_id == "special-id"


def test_contribution_element_type_propagated() -> None:
    """Kills build_contribution__mutmut_22/28 (element_type=None or deleted)."""
    contrib = _build_contribution(element_type="risks")
    assert contrib.element_type == "risks"


def test_contribution_bloom_level_propagated() -> None:
    """Kills build_contribution__mutmut_23/29 (bloom_level=None or deleted)."""
    contrib = _build_contribution(bloom_level="apply")
    assert contrib.bloom_level == "apply"


def test_contribution_content_token_count_propagated() -> None:
    """Kills build_contribution__mutmut_24/30 (content_token_count=None or deleted)."""
    contrib = _build_contribution(content_text="a b c d e")
    assert contrib.content_token_count == count_tokens("a b c d e")
    assert contrib.content_token_count > 0


def test_contribution_content_score_propagated() -> None:
    """Kills build_contribution__mutmut_25/31 (content_score=None or deleted)."""
    contrib = _build_contribution(content_text="a b c d e", content_multiplier=2.0)
    assert contrib.content_score == count_tokens("a b c d e") * 2.0


def test_contribution_empty_content_logs_empty_content_event() -> None:
    """Kills build_contribution__mutmut_6 (logger event replaced with None)."""
    with capture_logs() as cap:
        _build_contribution(content_text="")
    assert any(e.get("event") == "empty_content" for e in cap)
