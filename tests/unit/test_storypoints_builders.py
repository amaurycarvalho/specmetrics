from __future__ import annotations

from types import SimpleNamespace

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
    BuildMetadata as CfmBuildMeta,
)
from specmetrics.kernel.cfm.model import (
    EvidenceRef as CfmEvidenceRef,
)
from specmetrics.kernel.csm.model import (
    BuildMetadata as CsmBuildMeta,
)
from specmetrics.kernel.csm.model import (
    CanonicalSpecificationModel,
    Decision,
)
from specmetrics.kernel.csm.model import (
    EvidenceRef as CsmEvidenceRef,
)
from specmetrics.plugins.measurement.storypoints._builders import (
    build_cfm_non_fp_items,
    build_csm_items,
    build_fp_items,
)
from specmetrics.plugins.measurement.storypoints._refs import (
    evidence_ref_from_cfm_evidence,
    evidence_ref_from_csm_evidence,
    evidence_ref_from_fp,
    fingerprint,
)
from specmetrics.plugins.measurement.storypoints.calibrator import (
    StoryPointsCalibrationProfile,
)
from specmetrics.plugins.measurement.storypoints.token_counter import (
    count_tokens_for_element,
)


def _cal() -> StoryPointsCalibrationProfile:
    return StoryPointsCalibrationProfile()


class TestEvidenceRefFromFp:
    def test_with_attributes(self):
        ev = SimpleNamespace(
            graph_node_id="g1", document_id="d1", section_id="s1", text="txt"
        )
        ref = evidence_ref_from_fp(SimpleNamespace(evidence=ev))
        assert ref.graph_node_id == "g1"
        assert ref.document_id == "d1"
        assert ref.section_id == "s1"
        assert ref.text == "txt"

    def test_missing_attributes_defaults(self):
        ev = SimpleNamespace()
        ref = evidence_ref_from_fp(SimpleNamespace(evidence=ev))
        assert ref.graph_node_id == ""
        assert ref.document_id == ""
        assert ref.section_id is None
        assert ref.text == ""


class TestEvidenceRefFromCfmEvidence:
    def test_with_attributes(self):
        ev = SimpleNamespace(
            graph_node_id="g9", document_id="d9", section_id="s9", text="x"
        )
        ref = evidence_ref_from_cfm_evidence(ev)
        assert ref.graph_node_id == "g9"
        assert ref.document_id == "d9"
        assert ref.section_id == "s9"
        assert ref.text == "x"

    def test_missing_attributes_defaults(self):
        ref = evidence_ref_from_cfm_evidence(SimpleNamespace())
        assert ref.graph_node_id == ""
        assert ref.document_id == ""
        assert ref.section_id is None
        assert ref.text == ""


class TestEvidenceRefFromCsmEvidence:
    def test_first_ref_used(self):
        r = SimpleNamespace(
            graph_node_id="gc", document_id="dc", section_id="sc", text="tc"
        )
        other = SimpleNamespace(graph_node_id="gx", document_id="dx", text="tx")
        ref = evidence_ref_from_csm_evidence([r, other])
        assert ref.graph_node_id == "gc"
        assert ref.document_id == "dc"
        assert ref.section_id == "sc"
        assert ref.text == "tc"

    def test_nodes_has_id_fallback(self):
        r = SimpleNamespace(id="by-id", document_id="d", text="t")
        ref = evidence_ref_from_csm_evidence([r])
        assert ref.graph_node_id == "by-id"

    def test_empty_returns_none(self):
        assert evidence_ref_from_csm_evidence([]) is None
        assert evidence_ref_from_csm_evidence(None) is None

    def test_missing_attributes_defaults(self):
        ref = evidence_ref_from_csm_evidence([SimpleNamespace()])
        assert ref.graph_node_id == ""
        assert ref.document_id == ""
        assert ref.section_id is None
        assert ref.text == ""


class TestFingerprint:
    def _fp(self, ev: CfmEvidenceRef) -> FunctionalProcess:
        return FunctionalProcess(id="fp", name="A", evidence=ev)

    def test_stable_for_same_evidence(self):
        ev = CfmEvidenceRef(graph_node_id="g", document_id="d", section_id="s", text="t")
        fp = self._fp(ev)
        assert fingerprint(fp) == fingerprint(fp)

    def test_changes_when_text_changes(self):
        a = self._fp(CfmEvidenceRef(graph_node_id="g", document_id="d", section_id="s", text="aaa"))
        b = self._fp(CfmEvidenceRef(graph_node_id="g", document_id="d", section_id="s", text="bbb"))
        assert fingerprint(a) != fingerprint(b)

    def test_changes_when_document_changes(self):
        a = self._fp(CfmEvidenceRef(graph_node_id="g", document_id="d1", section_id="s", text="t"))
        b = self._fp(CfmEvidenceRef(graph_node_id="g", document_id="d2", section_id="s", text="t"))
        assert fingerprint(a) != fingerprint(b)


def _uid() -> str:
    import uuid

    return str(uuid.uuid4())


def _fp_evidence(text: str = "e") -> CfmEvidenceRef:
    return CfmEvidenceRef(
        graph_node_id="gn", document_id="doc", section_id="sec", text=text
    )


def _make_cfm(
    fps: list[FunctionalProcess],
    business_rules: dict[str, BusinessRule] | None = None,
    operations: dict[str, Operation] | None = None,
    data_groups: dict[str, DataGroup] | None = None,
    relationships: list[Relationship] | None = None,
    actors: dict[str, Actor] | None = None,
) -> CanonicalFunctionalModel:
    return CanonicalFunctionalModel(
        run_id="cfg-t",
        actors=actors or {},
        functional_processes={fp.id: fp for fp in fps},
        business_rules=business_rules or {},
        operations=operations or {},
        data_groups=data_groups or {},
        relationships=relationships or [],
        metadata=CfmBuildMeta(run_id="cfg-t", version="1.0", source="test"),
    )


class TestBuildFpItems:
    def test_item_metadata(self):
        ev = _fp_evidence()
        fp = FunctionalProcess(
            id=_uid(), name="Login", actor_ids=[], evidence=ev
        )
        cfm = _make_cfm([fp])
        items, _warnings, fp_count, merged, _seen = build_fp_items(
            cfm, _cal().factor_coefficients, None, 0.1, _cal()
        )
        assert fp_count == 1
        assert merged == 0
        assert len(items) == 1
        item = items[0]
        assert item.element_id == fp.id
        assert item.element_type == "functional_process"
        assert item.source_model == "CFM"
        assert item.normalized_value == 0
        assert item.rank_position == 0
        assert item.base_weight is None
        assert item.applied_rules == ["default_coefficients_v1"]
        assert len(item.evidence_refs) == 1
        assert item.evidence_refs[0].graph_node_id == "gn"
        assert abs(item.structural_score - sum(item.factor_breakdown.values())) < 0.001

    def test_custom_rules(self):
        ev = _fp_evidence()
        fp = FunctionalProcess(id=_uid(), name="P", actor_ids=[], evidence=ev)
        cfm = _make_cfm([fp])
        items, *_ = build_fp_items(
            cfm, _cal().factor_coefficients, {"business_interactions": 1.0}, 0.1,
            _cal(),
        )
        assert items[0].applied_rules == ["custom_coefficients:business_interactions=1.0"]

    def test_duplicate_fps_merged_counted(self):
        ev = _fp_evidence()
        fp1 = FunctionalProcess(id=_uid(), name="Dup", actor_ids=[], evidence=ev)
        fp2 = FunctionalProcess(id=_uid(), name="Dup", actor_ids=[], evidence=ev)
        fp3 = FunctionalProcess(id=_uid(), name="Dup", actor_ids=[], evidence=ev)
        cfm = _make_cfm([fp1, fp2, fp3])
        items, _warnings, fp_count, merged, _seen = build_fp_items(
            cfm, _cal().factor_coefficients, None, 0.1, _cal()
        )
        assert fp_count == 3
        assert merged == 2
        assert len(items) == 1


class TestBuildCsmItems:
    def _csm(self, decisions: dict | None = None, glossaries: dict | None = None):
        return CanonicalSpecificationModel(
            run_id="csm-t",
            decisions=decisions or {},
            glossary_terms=glossaries or {},
            metadata=CsmBuildMeta(run_id="csm-t", version="1.0", source="test"),
        )

    def _decision(self, description="desc", with_ref=True):
        refs = []
        if with_ref:
            refs = [CsmEvidenceRef(graph_node_id="gc", document_id="dc", text="t")]
        return Decision(id=_uid(), description=description, evidence_references=refs)

    def test_item_metadata(self):
        dec = self._decision()
        csm = self._csm(decisions={dec.id: dec})
        items, _warnings, csm_count = build_csm_items(csm, 0.1, _cal(), set())
        assert csm_count == 1
        item = items[0]
        assert item.element_type == "decision"
        assert item.source_model == "CSM"
        assert item.normalized_value == 0
        assert item.rank_position == 0
        assert item.applied_rules == ["csm_base_weight"]
        assert item.base_weight == _cal().csm_base_weights["decision"]
        assert item.content_tokens == count_tokens_for_element("decision", dec.description)
        assert abs(item.content_score - item.content_tokens * 0.1) < 0.001
        assert len(item.evidence_refs) == 1
        assert item.evidence_refs[0].graph_node_id == "gc"
        assert item.evidence_refs[0].document_id == "dc"

    def test_unknown_type_warning(self):
        dec = self._decision()
        csm = self._csm(decisions={dec.id: dec})
        cal = StoryPointsCalibrationProfile(csm_base_weights={})
        _items, warnings, _ = build_csm_items(csm, 0.1, cal, set())
        assert len(warnings) == 1
        assert warnings[0].code == "UNKNOWN_ELEMENT_TYPE"
        assert warnings[0].message == (
            f"Element type 'decision' not in csm_base_weights, "
            f"using default_fallback_weight={cal.default_fallback_weight}"
        )
        assert warnings[0].element_id == dec.id

    def test_known_type_with_default_weight_no_warning(self):
        dec = self._decision()
        csm = self._csm(decisions={dec.id: dec})
        cal = StoryPointsCalibrationProfile(
            csm_base_weights={"decision": 1.0}
        )
        _items, warnings, _ = build_csm_items(csm, 0.1, cal, set())
        assert len(warnings) == 0

    def test_missing_evidence_gives_empty_refs(self):
        dec = self._decision(with_ref=False)
        csm = self._csm(decisions={dec.id: dec})
        items, _warnings, _ = build_csm_items(csm, 0.1, _cal(), set())
        assert items[0].evidence_refs == []

    def test_name_truncated_to_eighty(self):
        desc = "x" * 85
        dec = self._decision(description=desc)
        csm = self._csm(decisions={dec.id: dec})
        items, *_ = build_csm_items(csm, 0.1, _cal(), set())
        assert len(items[0].element_name) == 80

    def test_content_score_uses_multiplier(self):
        dec = self._decision()
        csm = self._csm(decisions={dec.id: dec})
        items, *_ = build_csm_items(csm, 0.5, _cal(), set())
        expected = count_tokens_for_element("decision", dec.description) * 0.5
        assert abs(items[0].content_score - expected) < 0.001


class TestBuildCfmNonFpItems:
    def test_counts_and_item_metadata(self):
        ev = _fp_evidence()
        brid = _uid()
        br = BusinessRule(
            id=brid, name="BR", related_process_ids=[], evidence=ev
        )
        oid = _uid()
        op = Operation(id=oid, name="Op", parent_process_id=_uid(), evidence=ev)
        dgid = _uid()
        dg = DataGroup(id=dgid, name="DG", evidence=ev)
        aid = _uid()
        act = Actor(id=aid, name="Actor", evidence=ev)
        rel = Relationship(
            id=_uid(), source_id="a", target_id="b",
            relationship_type="communicates_with", evidence=ev,
        )
        cfm = _make_cfm(
            [],
            business_rules={brid: br},
            operations={oid: op},
            data_groups={dgid: dg},
            relationships=[rel],
            actors={aid: act},
        )
        items, _warnings, non_fp_count, no_weight = build_cfm_non_fp_items(
            cfm, 0.1, StoryPointsCalibrationProfile(default_fallback_weight=0.0), set()
        )
        types = sorted(i.element_type for i in items)
        assert types == [
            "actor", "business_rule", "data_group", "operation", "relationship",
        ]
        assert non_fp_count == 5
        assert no_weight == 0
        for item in items:
            assert item.source_model == "CFM"
            assert item.normalized_value == 0
            assert item.base_weight is not None
            assert item.applied_rules == ["cfm_base_weight"]
            assert item.factor_breakdown == {}

    def test_fallback_weight_counted(self):
        ev = _fp_evidence()
        br = BusinessRule(id=_uid(), name="R", related_process_ids=[], evidence=ev)
        cfm = _make_cfm([], business_rules={br.id: br})
        cal = StoryPointsCalibrationProfile(cfm_base_weights={})
        items, _warnings, non_fp_count, no_weight = build_cfm_non_fp_items(
            cfm, 0.1, cal, set()
        )
        assert non_fp_count == 1
        assert no_weight == 1
        assert items[0].base_weight == cal.default_fallback_weight


def test_cfm_weighted_item_metadata():
    """Mutmut 8/9/39/43/44/47/48/49/50/51: weighted item metadata is exact."""
    ev = _fp_evidence()
    br = BusinessRule(
        id=_uid(),
        name="Rule A",
        description="long description text here",
        related_process_ids=[],
        evidence=ev,
    )
    cfm = _make_cfm([], business_rules={br.id: br})
    cal = _cal()
    items, _warnings, non_fp_count, no_weight = build_cfm_non_fp_items(
        cfm, 0.1, cal, set()
    )
    assert non_fp_count == 1
    assert no_weight == 0
    item = items[0]
    assert item.source_model == "CFM"
    assert item.normalized_value == 0
    assert item.rank_position == 0
    assert item.factor_breakdown == {}
    assert item.applied_rules == ["cfm_base_weight"]
    assert item.content_tokens == count_tokens_for_element(br.name, br.description)
    assert len(item.evidence_refs) == 1
    assert item.evidence_refs[0].document_id == "doc"
    assert item.evidence_refs[0].graph_node_id == "gn"


def test_cfm_weighted_item_fallback_returns_inc_no_weight():
    """Mutmut 5/52/53/54: fallback-weighted items report no_weight=1 and base_weight."""
    ev = _fp_evidence()
    br = BusinessRule(id=_uid(), name="R", related_process_ids=[], evidence=ev)
    cfm = _make_cfm([], business_rules={br.id: br})
    cal = StoryPointsCalibrationProfile(cfm_base_weights={})
    items, _warnings, non_fp_count, no_weight = build_cfm_non_fp_items(
        cfm, 0.1, cal, set()
    )
    assert non_fp_count == 1
    assert no_weight == 1
    assert items[0].base_weight == cal.default_fallback_weight


def test_cfm_weighted_item_known_weight_no_no_weight():
    """Mutmut 55/56: known-weight items must not be reported as without weight."""
    ev = _fp_evidence()
    br = BusinessRule(id=_uid(), name="BR", related_process_ids=[], evidence=ev)
    cfm = _make_cfm([], business_rules={br.id: br})
    _items, _warnings, non_fp_count, no_weight = build_cfm_non_fp_items(
        cfm, 0.1, _cal(), set()
    )
    assert non_fp_count == 1
    assert no_weight == 0