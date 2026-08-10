from __future__ import annotations

import hashlib
from types import SimpleNamespace

from specmetrics.kernel.cfm.model import EvidenceRef as CFMEvidenceRef
from specmetrics.kernel.cfm.model import Operation
from specmetrics.plugins.measurement.snap.assessor import SNAPAssessor
from specmetrics.plugins.measurement.snap.models import (
    AssessedItem,
    RulePack,
)


def _op(
    elem_id: str,
    marker: str,
    doc_id: str = "doc-1",
    section_id: str | None = "sec-1",
    text: str = "ev",
) -> Operation:
    return Operation(
        id=elem_id,
        name=f"name-{elem_id}",
        parent_process_id="fp-1",
        evidence=CFMEvidenceRef(
            graph_node_id=f"g-{elem_id}",
            document_id=doc_id,
            section_id=section_id,
            text=text,
        ),
        metadata={"semantic_marker": marker},
    )


def _item(elem_id: str, marker: str = "presentation_interface") -> AssessedItem:
    return AssessedItem(
        id="snap-item-1",
        name=f"name-{elem_id}",
        category_id="presentation",
        contribution=4.0,
        cfm_element_id=elem_id,
        cfm_semantic_marker=marker,
    )


def _assessor() -> SNAPAssessor:
    return SNAPAssessor()


def _empty_config():
    return _assessor()._build_rule_pack_config(None)


class TestBuildRulePackConfig:
    def test_none_rule_pack_returns_default(self) -> None:
        config = _assessor()._build_rule_pack_config(None)
        assert config.excluded_categories == set()
        assert config.contribution_overrides == {}
        assert config.inclusion_overrides == {}
        assert config.exclusion_by_id == set()
        assert config.exclusion_patterns == []

    def test_populates_excluded_categories_and_overrides(self) -> None:
        rp = RulePack(
            id="rp",
            excluded_categories=["presentation"],
            contribution_overrides={"data_operations": 5.0},
        )
        config = _assessor()._build_rule_pack_config(rp)
        assert config.excluded_categories == {"presentation"}
        assert config.contribution_overrides == {"data_operations": 5.0}

    def test_populates_inclusion_overrides_from_policies(self) -> None:
        rp = RulePack(
            id="rp",
            inclusion_policies=[
                {"semantic_marker": "custom_signal", "category": "data_operations"},
                {"semantic_marker": "x", "category": ""},
                {"semantic_marker": "", "category": "presentation"},
            ],
        )
        config = _assessor()._build_rule_pack_config(rp)
        assert config.inclusion_overrides == {"custom_signal": "data_operations"}

    def test_populates_item_exclusions(self) -> None:
        rp = RulePack(
            id="rp",
            item_exclusions={"by_id": ["op-1"], "by_pattern": ["*_internal_*"]},
        )
        config = _assessor()._build_rule_pack_config(rp)
        assert config.exclusion_by_id == {"op-1"}
        assert config.exclusion_patterns == ["*_internal_*"]


class TestResolveAssignment:
    def test_missing_semantic_marker_warns(self) -> None:
        op = _op("op-1", "")
        warnings = []
        result = _assessor()._resolve_assignment(
            "op-1", op, _empty_config(), warnings
        )
        assert result is None
        assert warnings[0].code == "MISSING_SEMANTIC_MARKER"
        assert warnings[0].cfm_element_id == "op-1"

    def test_unsupported_marker_warns(self) -> None:
        op = _op("op-1", "totally_unknown_marker")
        rp = RulePack(id="rp", inclusion_policies=[])
        config = _assessor()._build_rule_pack_config(rp)
        warnings = []
        result = _assessor()._resolve_assignment("op-1", op, config, warnings)
        assert result is None
        assert warnings[0].code == "UNSUPPORTED_MARKER"
        assert warnings[0].details == {"marker": "totally_unknown_marker"}

    def test_inclusion_override_allows_unsupported_marker(self) -> None:
        op = _op("op-1", "custom_signal")
        rp = RulePack(
            id="rp",
            inclusion_policies=[
                {"semantic_marker": "custom_signal", "category": "presentation"}
            ],
        )
        config = _assessor()._build_rule_pack_config(rp)
        warnings = []
        result = _assessor()._resolve_assignment("op-1", op, config, warnings)
        assert warnings == []
        assert result == ("custom_signal", "presentation", 4.0)

    def test_excluded_category_returns_none(self) -> None:
        op = _op("op-1", "presentation_interface")
        rp = RulePack(id="rp", excluded_categories=["presentation"])
        config = _assessor()._build_rule_pack_config(rp)
        assert _assessor()._resolve_assignment("op-1", op, config, []) is None

    def test_contribution_override_applied(self) -> None:
        op = _op("op-1", "data_operation")
        rp = RulePack(
            id="rp", contribution_overrides={"data_operations": 9.0}
        )
        config = _assessor()._build_rule_pack_config(rp)
        semantic_marker, category_id, contribution = _assessor()._resolve_assignment(
            "op-1", op, config, []
        )
        assert semantic_marker == "data_operation"
        assert category_id == "data_operations"
        assert contribution == 9.0


class TestEvidenceRefsAndFingerprint:
    def test_evidence_refs_maps_cfm_evidence(self) -> None:
        op = _op("op-1", "presentation_interface", "doc-9", "sec-9", "hello")
        refs = _assessor()._evidence_refs(op)
        assert len(refs) == 1
        assert refs[0].document_id == "doc-9"
        assert refs[0].section_id == "sec-9"
        assert refs[0].text == "hello"
        assert refs[0].graph_node_id == "g-op-1"

    def test_evidence_refs_none_returns_empty(self) -> None:
        class NoEvidence:
            pass

        assert _assessor()._evidence_refs(NoEvidence()) == []

    def test_fingerprint_uses_evidence_and_marker(self) -> None:
        a = _op("op-1", "presentation_interface", "doc-1", "sec-1", "same")
        b = _op("op-1", "presentation_interface", "doc-1", "sec-1", "same")
        assert _assessor()._fingerprint("op-1", a) == _assessor()._fingerprint(
            "op-1", b
        )

    def test_fingerprint_differs_with_different_evidence(self) -> None:
        a = _op("op-1", "presentation_interface", "doc-1", None, "t1")
        b = _op("op-1", "presentation_interface", "doc-2", None, "t1")
        assert _assessor()._fingerprint("op-1", a) != _assessor()._fingerprint(
            "op-1", b
        )


class TestDeduplicate:
    def test_first_item_recorded(self) -> None:
        seen: dict[str, str] = {}
        op = _op("op-1", "presentation_interface")
        item, warning = _assessor()._deduplicate(_item("op-1"), seen, "op-1", op)
        assert warning is None
        assert item is not None
        assert len(seen) == 1

    def test_duplicate_merged_and_warns(self) -> None:
        seen: dict[str, str] = {}
        assessor = _assessor()
        op = _op("op-1", "presentation_interface")
        first, _ = assessor._deduplicate(_item("op-1"), seen, "op-1", op)
        assert first is not None
        item, warning = assessor._deduplicate(_item("op-2"), seen, "op-1", op)
        assert item is None
        assert warning is not None
        assert warning.code == "DUPLICATE_MERGED"
        assert warning.details == {"merged_into": first.id}


class TestCheckExclusion:
    def test_by_id_excludes(self) -> None:
        item = _item("op-1")
        _, warning = _assessor()._check_exclusion(
            item, "op-1", _op("op-1", "presentation_interface"),
            {"op-1"}, [], None,
        )
        assert item.excluded is True
        assert item.contribution == 0.0
        assert item.rule_applied == "excluded_by_id"
        assert warning is not None
        assert warning.code == "ITEM_EXCLUDED"
        assert warning.cfm_element_id == "op-1"

    def test_by_pattern_matches_elem_id(self) -> None:
        item = _item("op-1")
        _assessor()._check_exclusion(
            item, "op-internal-1", _op("op-internal-1", "presentation_interface"),
            set(), ["*internal*"], None,
        )
        assert item.excluded is True
        assert item.contribution == 0.0
        assert item.rule_applied == "excluded_by_pattern:*internal*"

    def test_by_pattern_matches_elem_name(self) -> None:
        item = _item("op-1")
        op = _op("op-1", "presentation_interface")
        op.name = "internal-op"
        _assessor()._check_exclusion(
            item, "op-1", op, set(), ["*internal*"], None,
        )
        assert item.excluded is True
        assert item.rule_applied == "excluded_by_pattern:*internal*"

    def test_no_exclusion(self) -> None:
        item = _item("op-1")
        flag, warning = _assessor()._check_exclusion(
            item, "op-1", _op("op-1", "presentation_interface"),
            set(), [], None,
        )
        assert flag is False
        assert warning is None
        assert item.excluded is False
        assert item.contribution == 4.0


def test_build_rule_pack_config_missing_by_id_key_defaults_empty_set() -> None:
    """Mutmut 20/22: item_exclusions without 'by_id' must yield an empty set."""
    rp = RulePack(id="rp", item_exclusions={"by_pattern": ["*_internal_*"]})
    config = _assessor()._build_rule_pack_config(rp)
    assert config.exclusion_by_id == set()
    assert config.exclusion_patterns == ["*_internal_*"]


def test_process_element_increments_counter_and_sets_element_id() -> None:
    """Mutmut 2/13/14/25/29/30/34/35/45/48: _process_element must forward elem_id."""
    assessor = _assessor()
    op = _op("op-1", "presentation_interface")
    config = _empty_config()
    seen: dict[str, str] = {}
    warnings: list = []
    item, counter = assessor._process_element("op-1", op, config, seen, 5, warnings)
    assert counter == 6
    assert item is not None
    assert item.cfm_element_id == "op-1"
    assert item.name == "name-op-1"
    assert item.category_id == "presentation"


def test_resolve_assignment_missing_marker_key_warns() -> None:
    """Mutmut 3/5: a missing 'semantic_marker' key triggers MISSING_SEMANTIC_MARKER."""
    op = _op("op-1", "presentation_interface")
    op.metadata = {}
    warnings: list = []
    result = _assessor()._resolve_assignment("op-1", op, _empty_config(), warnings)
    assert result is None
    assert warnings[0].code == "MISSING_SEMANTIC_MARKER"
    assert warnings[0].message == "Element 'op-1' has no semantic metadata marker"


def test_fingerprint_exact_hash_without_evidence() -> None:
    """Mutmut 6/10/12/14/16/18/19/20/21/22/23/27/28/32: fingerprint uses empty defaults."""
    elem = SimpleNamespace(metadata={"semantic_marker": "presentation_interface"})
    fp = _assessor()._fingerprint("elem-1", elem)
    raw = "elem-1::::presentation_interface"
    assert fp == hashlib.sha256(raw.encode()).hexdigest()


def test_fingerprint_exact_hash_with_evidence() -> None:
    """Mutmut 11/13/15/31: fingerprint embeds evidence values verbatim."""
    op = _op("elem-1", "presentation_interface", "doc-9", "sec-9", "hello")
    fp = _assessor()._fingerprint("elem-1", op)
    raw = "elem-1:doc-9:sec-9:hello:presentation_interface"
    assert fp == hashlib.sha256(raw.encode()).hexdigest()


def test_fingerprint_missing_marker_key_uses_empty_default() -> None:
    """Mutmut 17/19/22: absent marker key contributes an empty string to the hash."""
    elem = SimpleNamespace(metadata={})
    fp = _assessor()._fingerprint("elem-2", elem)
    raw = "elem-2::::"
    assert fp == hashlib.sha256(raw.encode()).hexdigest()


def test_deduplicate_uses_element_fingerprint() -> None:
    """Mutmut 3: fingerprinting must depend on the element, not on None."""
    assessor = _assessor()
    seen: dict[str, str] = {}
    op_a = _op("op-1", "presentation_interface", "doc-1", "sec-1", "ta")
    op_b = _op("op-1", "presentation_interface", "doc-2", "sec-1", "ta")
    item_a, _ = assessor._deduplicate(_item("op-1"), seen, "op-1", op_a)
    item_b, warning = assessor._deduplicate(_item("op-1"), seen, "op-1", op_b)
    assert item_a is not None
    assert item_b is not None
    assert warning is None


def test_deduplicate_warning_reports_merged_element_id() -> None:
    """Mutmut 9/13: duplicate warning must carry the duplicate item's element id."""
    assessor = _assessor()
    seen: dict[str, str] = {}
    op = _op("op-1", "presentation_interface")
    first, _ = assessor._deduplicate(_item("op-1"), seen, "op-1", op)
    assert first is not None
    item, warning = assessor._deduplicate(_item("op-2"), seen, "op-1", op)
    assert item is None
    assert warning is not None
    assert warning.cfm_element_id == "op-2"


def test_check_exclusion_by_id_returns_true_flag() -> None:
    """Mutmut 9/42/49/50: by-id exclusion returns True and ITEM_EXCLUDED."""
    item = _item("op-1")
    flag, warning = _assessor()._check_exclusion(
        item, "op-1", _op("op-1", "presentation_interface"), {"op-1"}, [], None,
    )
    assert flag is True
    assert warning is not None
    assert warning.code == "ITEM_EXCLUDED"
    assert warning.cfm_element_id == "op-1"


def test_check_exclusion_pattern_no_match_without_name_attr() -> None:
    """Mutmut 21/24: element without a name attribute must not crash on patterns."""
    item = _item("op-1")
    elem = SimpleNamespace()
    flag, warning = _assessor()._check_exclusion(
        item, "op-1", elem, set(), ["*nomatch*"], None,
    )
    assert flag is False
    assert warning is None
    assert item.excluded is False


def test_check_exclusion_missing_name_defaults_empty_string() -> None:
    """Mutmut 27: missing name attribute must default to the empty string."""
    item = _item("op-1")
    elem = SimpleNamespace()
    flag, warning = _assessor()._check_exclusion(
        item, "op-1", elem, set(), ["*XXXX*"], None,
    )
    assert flag is False
    assert warning is None