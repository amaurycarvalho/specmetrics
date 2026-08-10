from __future__ import annotations

import hashlib

import pytest

from specmetrics.kernel.cfm.model import EvidenceRef, Operation
from specmetrics.plugins.measurement.sfp._config import _ComponentSpec
from specmetrics.plugins.measurement.sfp._processing import _ComponentProcessor
from specmetrics.plugins.measurement.sfp.models import (
    MeasuredComponent,
    MeasurementSummary,
    SFPMeasurementResult,
)


def _make_evidence(node_type: str | None = None) -> EvidenceRef:
    section_id = None if node_type is None else "s1"
    return EvidenceRef(
        graph_node_id="gn-001",
        document_id="doc-001",
        section_id=section_id,
        text="some text",
    )


def _make_operation(
    op_id: str,
    node_type: str | None = "elementary_process",
    evidence: EvidenceRef | None = None,
) -> Operation:
    meta = {}
    if node_type:
        meta["node_type"] = node_type
    return Operation(
        id=op_id,
        name="Create",
        parent_process_id="fp-001",
        evidence=evidence or _make_evidence(),
        metadata=meta,
    )


def _make_component(
    cid: str,
    element_id: str,
    contribution: float = 4.6,
    component_type: str = "functional_process",
) -> MeasuredComponent:
    return MeasuredComponent(
        id=cid,
        name="comp",
        component_type=component_type,
        contribution=contribution,
        cfm_element_id=element_id,
        cfm_element_type="Operation",
    )


def _fp_spec(node_types: set[str] | None = None) -> _ComponentSpec:
    return _ComponentSpec(
        excluded_name="functional_process",
        contribution=4.6,
        node_types=node_types or set(),
        element_type_name="Operation",
        component_type="functional_process",
    )


class TestIsIncluded:
    def test_include_by_id(self):
        proc = _ComponentProcessor()
        assert proc._is_included("op-001", "x", {"op-001"}, []) is True

    def test_include_by_id_not_matched(self):
        proc = _ComponentProcessor()
        assert proc._is_included("op-002", "x", set(), []) is False

    def test_include_by_pattern_matches_id(self):
        proc = _ComponentProcessor()
        assert proc._is_included("op-001", "nomatch", set(), ["op-*"]) is True

    def test_include_by_pattern_matches_name(self):
        proc = _ComponentProcessor()
        assert proc._is_included("nope", "op_target", set(), ["op_*"]) is True


class TestIsExcluded:
    def test_exclude_by_id(self):
        proc = _ComponentProcessor()
        assert proc._is_excluded("op-001", "x", {"op-001"}, []) is True

    def test_exclude_pattern_matches_id_and_not_name(self):
        proc = _ComponentProcessor()
        assert proc._is_excluded("op-001", "plainname", set(), ["op-*"]) is True

    def test_exclude_pattern_matches_name_and_not_id(self):
        proc = _ComponentProcessor()
        assert proc._is_excluded("abc", "*_int_*", set(), ["*_int_*"]) is True

    def test_no_exclusion(self):
        proc = _ComponentProcessor()
        assert proc._is_excluded("abc", "def", set(), ["op-*"]) is False


class TestProcessElement:
    def test_excludes_by_name_pattern(self):
        proc = _ComponentProcessor()
        op = _make_operation("op-001", node_type="elementary_process")
        spec = _fp_spec()
        components = []
        warnings = []
        proc._process_element(
            op=op,
            spec=spec,
            excluded=set(),
            excluded_ids=set(),
            excluded_patterns=["*reate*"],
            included_ids=set(),
            included_patterns=[],
            components=components,
            warnings=warnings,
            seen_fingerprints={},
        )
        assert len(components) == 0


class TestIsElement:
    def test_node_type_in_spec(self):
        proc = _ComponentProcessor()
        op = _make_operation("op-001", node_type="custom_process")
        assert proc._is_element(op, _fp_spec({"custom_process"})) is True

    def test_node_type_missing_in_spec(self):
        proc = _ComponentProcessor()
        op = _make_operation("op-001", node_type="other_process")
        assert proc._is_element(op, _fp_spec({"custom_process"})) is False

    def test_no_node_types_uses_operation_default(self):
        proc = _ComponentProcessor()
        op = _make_operation("op-001", node_type="elementary_process")
        assert proc._is_element(op, _fp_spec()) is True

    def test_no_node_types_with_non_elementary(self):
        proc = _ComponentProcessor()
        op = _make_operation("op-001", node_type="internal_step")
        assert proc._is_element(op, _fp_spec()) is False


class TestFingerprint:
    def test_fingerprint_normalizes_missing_section(self):
        proc = _ComponentProcessor()
        ev = EvidenceRef(
            graph_node_id="gn-001",
            document_id="doc-001",
            section_id=None,
            text="some text",
        )
        op = _make_operation("op-001", node_type=None, evidence=ev)
        raw = "doc-001::some text:Operation"
        assert proc._fingerprint(op) == hashlib.sha256(raw.encode()).hexdigest()


class TestMergePrevious:
    def test_merge_none_inputs_are_noops(self):
        proc = _ComponentProcessor()
        components = [_make_component("c-1", "a")]
        proc._merge_previous(components, None, ["a"])
        assert len(components) == 1

    def test_merge_both_provided_appends_unmodified(self):
        proc = _ComponentProcessor()
        components = [_make_component("c-1", "a")]
        prev = SFPMeasurementResult(
            run_id="r",
            cfm_run_id="x",
            measured_components=[_make_component("p-1", "a"), _make_component("p-2", "b")],
            summary=MeasurementSummary(total_component_count=2, total_sfp=9.2),
        )
        proc._merge_previous(components, prev, ["a"])
        assert len(components) == 2
        assert all(isinstance(c, MeasuredComponent) for c in components)

    def test_merge_skips_previously_modified(self):
        proc = _ComponentProcessor()
        components = [_make_component("c-1", "a")]
        prev = SFPMeasurementResult(
            run_id="r",
            cfm_run_id="x",
            measured_components=[_make_component("p-1", "b")],
            summary=MeasurementSummary(total_component_count=1, total_sfp=4.6),
        )
        proc._merge_previous(components, prev, ["b"])
        assert len(components) == 1


class TestCreateComponent:
    def test_creates_component_with_section(self):
        proc = _ComponentProcessor()
        ev = _make_evidence(node_type="x")
        op = _make_operation("op-001", node_type="elementary_process", evidence=ev)
        comp = proc._create_component(
            element=op,
            element_id="op-001",
            element_name="Create Order",
            element_type_name="Operation",
            component_type="functional_process",
            contribution=4.6,
            component_counter=1,
        )
        assert comp.evidence_refs[0].section_id == "s1"
        assert comp.id == "cmp-functional_process-1"


class TestDeduplicate:
    def test_duplicate_merge_warning(self):
        proc = _ComponentProcessor()
        seen: dict[str, str] = {}
        first = _make_component("cmp-1", "a")
        second = _make_component("cmp-2", "b")
        kept, _ = proc._deduplicate(first, seen, "FP")
        assert kept is first
        dropped, warning = proc._deduplicate(second, seen, "FP")
        assert dropped is None
        assert warning is not None
        assert warning.cfm_element_id == "b"
        assert warning.details == {"merged_into": "cmp-1"}


class TestBuildSummary:
    def test_builds_typed_summary(self):
        proc = _ComponentProcessor()
        components = [
            _make_component("f1", "a"),
            _make_component("f2", "b"),
            _make_component(
                "l1", "c", contribution=7.1, component_type="logical_function"
            ),
        ]
        summary = proc._build_summary(components)
        assert summary.total_component_count == 3
        assert summary.total_sfp == pytest.approx(16.3)
        assert summary.by_type["functional_process"].count == 2
        assert summary.by_type["functional_process"].total_sfp == 9.2
        assert summary.by_type["logical_function"].count == 1
        assert summary.by_type["logical_function"].total_sfp == 7.1