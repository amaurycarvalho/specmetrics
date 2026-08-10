from __future__ import annotations

from pathlib import Path

from specmetrics.application.entity_builders import (
    _build_metric_entry,
    _build_stage_entities,
    _coerce_element_dict,
    _coerce_element_evidence,
    _coerce_element_obj,
    _entities_for_cfm,
    _entities_for_csm,
    _entities_for_discover,
    _entities_for_export,
    _entities_for_extract,
    _entities_for_graph,
    _entities_for_measure,
    _entities_for_rule,
    _metric_breakdown,
    _metric_warnings,
)
from specmetrics.kernel.events import EventType


class _Ctx:
    def __init__(self, **kwargs: object) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


class _Doc:
    def __init__(self, id: str = "", document_type: str = "", path: str = "") -> None:
        self.id = id
        self.document_type = document_type
        self.path = path


class _Elem:
    def __init__(self, **kwargs: object) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_build_stage_entities_skips_unknown_stage():
    """Kills mutmut_25 (stage_name None), mutmut_27 (stage_name membership), mutmut_28 (continue->break)."""
    ctx = _Ctx()
    entities = _build_stage_entities(ctx, [], None)
    assert entities == {}


def test_build_stage_entities_missing_builder():
    """Kills mutmut_29/30 (builder get), mutmut_31/32 (builder call)."""
    ctx = _Ctx()
    entities = _build_stage_entities(ctx, [], None)
    assert entities == {}


def test_build_stage_entities_populates_stages():
    """Kills mutmut_25/27/28 in the loop by exercising a valid stage."""
    ctx = _Ctx(adapter_result={"documents": [{"id": "d"}]})
    entities = _build_stage_entities(ctx, [EventType.REPOSITORY_LOADED], None)
    assert entities["discover"] == [{"id": "", "document_type": "", "path": ""}]


def test_entities_for_discover_no_result():
    """Kills mutmut_2/3/7/8/9 (adapter_data getattr), mutmut_16/17/18 (id getattr)."""
    ctx = _Ctx()
    assert _entities_for_discover(ctx) == []


def test_entities_for_discover_documents():
    """Kills mutmut_28/29/30 (document_type), mutmut_40/41/42 (path), mutmut_46-51 (documents get)."""
    ctx = _Ctx(
        adapter_result={
            "documents": [
                _Doc(id="d1", document_type="spec", path="spec.md"),
                _Doc(id="d2"),
            ]
        }
    )
    entities = _entities_for_discover(ctx)
    assert entities[0] == {"id": "d1", "document_type": "spec", "path": "spec.md"}
    assert entities[1] == {"id": "d2", "document_type": "", "path": ""}


def test_entities_for_discover_dict_documents():
    """Kills mutmut_46-51 for dict-style documents."""
    ctx = _Ctx(
        adapter_result={"documents": [{"id": "d3", "document_type": "spec", "path": "p"}]}
    )
    entities = _entities_for_discover(ctx)
    assert entities[0] == {"id": "", "document_type": "", "path": ""}


def test_entities_for_extract_no_result():
    """Kills mutmut_2/3/7/8/9 (extract_data getattr)."""
    ctx = _Ctx()
    result = _entities_for_extract(ctx)
    assert result == [
        {"type": "documents_processed", "count": 0},
        {"type": "documents_skipped", "count": 0},
    ]


def test_entities_for_extract_dict_elements():
    """Kills mutmut_13/... (results get), coercion of dict elements."""
    ctx = _Ctx(
        extraction_result={
            "results": {
                "p1": {
                    "elements": [
                        {"id": "e1", "type": "actor", "content": "text", "confidence": 0.8},
                    ]
                }
            },
            "documents_processed": 2,
            "documents_skipped": 1,
        }
    )
    result = _entities_for_extract(ctx)
    assert result[0]["id"] == "e1"
    assert result[0]["type"] == "actor"
    assert result[0]["confidence"] == 0.8
    assert result[1] == {"type": "documents_processed", "count": 2}
    assert result[2] == {"type": "documents_skipped", "count": 1}


def test_entities_for_extract_obj_elements():
    """Kills obj-coercion branches."""
    ctx = _Ctx(
        extraction_result={
            "results": {
                "p1": {"elements": [_Elem(id="e2", type="operation", content="c", confidence=0.5)]}
            }
        }
    )
    result = _entities_for_extract(ctx)
    assert result[0]["id"] == "e2"
    assert result[0]["type"] == "operation"
    assert result[0]["confidence"] == 0.5


def test_entities_for_extract_skips_empty_elements():
    """Kills the empty-entry continue branch."""
    ctx = _Ctx(extraction_result={"results": {"p1": {"elements": [{}]}}})
    result = _entities_for_extract(ctx)
    assert len(result) == 2


def test_coerce_element_dict():
    """Kills _coerce_element_dict default and evidence branches."""
    entry = _coerce_element_dict({"id": "x", "type": "t", "content": "c", "confidence": 0.9, "evidence": {"document_id": "d"}})
    assert entry["id"] == "x"
    assert entry["type"] == "t"
    assert entry["confidence"] == 0.9
    assert entry["evidence"] == {"document_id": "d", "section_id": "None", "text": None}


def test_coerce_element_obj():
    """Kills _coerce_element_obj getattr branches."""
    entry = _coerce_element_obj(_Elem(id="y", type="u", content="c2", confidence=1.0))
    assert entry["id"] == "y"
    assert entry["type"] == "u"
    assert entry["confidence"] == 1.0
    assert entry["evidence"] == {}


def test_coerce_element_evidence_dict():
    """Kills evidence dict branches."""
    ev = _coerce_element_evidence({"document_id": "d", "section_id": "s", "text": "t"})
    assert ev == {"document_id": "d", "section_id": "s", "text": "t"}


def test_coerce_element_evidence_obj():
    """Kills evidence obj branches."""
    ev = _coerce_element_evidence(_Elem(document_id="d2", section_id="s2", text="t2"))
    assert ev == {"document_id": "d2", "section_id": "s2", "text": "t2"}


def test_entities_for_graph_no_result():
    """Kills graph_data getattr default."""
    assert _entities_for_graph(_Ctx()) == [
        {"node_type": "graph_summary", "edge_count": 0, "run_id": ""}
    ]


def test_entities_for_graph_nodes():
    """Kills node dict get branches."""
    ctx = _Ctx(
        evidence_graph={
            "nodes": [{"id": "n1", "node_type": "evidence", "text": "t"}],
            "edge_count": 3,
            "run_id": "r1",
        }
    )
    result = _entities_for_graph(ctx)
    assert result[0]["id"] == "n1"
    assert result[0]["node_type"] == "evidence"
    assert result[0]["text"] == "t"
    assert result[1] == {"node_type": "graph_summary", "edge_count": 3, "run_id": "r1"}


def test_build_metric_entry_total():
    """Kills _build_metric_entry total and breakdown branches."""
    mr = {
        "fpa_total_function_points": 10,
        "fpa_breakdown": [{"x": 1}],
        "cognitive_raw_score": 5.55,
        "cognitive_bloom_breakdown": {"L1": {"total": 3.33}},
        "function_points_warnings": [{"message": "w"}],
    }
    entry = _build_metric_entry(mr, "function_points", {"function_points": ("fpa_total_function_points", "fpa_breakdown")}, {"function_points": "function_points"})
    assert entry["metric"] == "function_points"
    assert entry["total"] == 10
    assert entry["status"] == "completed"
    assert entry["breakdown"] == [{"x": 1}]
    assert entry["warnings"] == ["w"]


def test_build_metric_entry_rounds_scores():
    """Kills the rounding branch for token/cognitive points."""
    mr = {"cognitive_raw_score": 5.55}
    entry = _build_metric_entry(mr, "cognitive_points", {"cognitive_points": ("cognitive_raw_score", None)}, {})
    assert entry["total"] == 5.5


def test_build_metric_entry_missing_key():
    """Kills the missing-key branch."""
    entry = _build_metric_entry({}, "snap", {"snap": ("snap_total_snap", None)}, {})
    assert entry["total"] == 0


def test_metric_breakdown_rounds_cognitive():
    """Kills the cognitive breakdown rounding branch."""
    bd = _metric_breakdown({"x": {"total": 3.33}}, "cognitive_points", "x")
    assert bd == {"total": 3.3}


def test_metric_warnings_non_list():
    """Kills the non-list warnings branch."""
    assert _metric_warnings({"fpa_warnings": "bad"}, "fpa") == []


def test_metric_warnings_list():
    """Kills warning coercion branches."""
    assert _metric_warnings({"fpa_warnings": [{"message": "a"}, "b"]}, "fpa") == ["a", "b"]


def test_entities_for_export_none_path():
    """Kills the export_path None early return."""
    assert _entities_for_export(_Ctx(), None) == []


def test_entities_for_export_relative():
    """Kills the relative_to branch."""
    ctx = _Ctx(repository=Path("/repo"))
    result = _entities_for_export(ctx, Path("/repo/out.json"))
    assert result == [{"format": "json", "path": "out.json"}]


def _cfm_evidence():
    from specmetrics.kernel.cfm.model import EvidenceRef

    return EvidenceRef(graph_node_id="gn1", document_id="doc1", text="ev")


def _make_cfm(**metadata_kwargs):
    from specmetrics.kernel.cfm.metadata import BuildMetadata
    from specmetrics.kernel.cfm.model import (
        Actor,
        CanonicalFunctionalModel,
        DataGroup,
        FunctionalProcess,
        Relationship,
    )

    metadata = BuildMetadata(run_id="cfm-run", **metadata_kwargs)
    return CanonicalFunctionalModel(
        run_id="cfm-run",
        actors={
            "a1": Actor(id="a1", name="User", evidence=_cfm_evidence()),
        },
        functional_processes={
            "fp1": FunctionalProcess(
                id="fp1", name="Login", actor_ids=["a1"], evidence=_cfm_evidence()
            ),
        },
        data_groups={
            "dg1": DataGroup(id="dg1", name="Orders", evidence=_cfm_evidence()),
        },
        relationships=[
            Relationship(
                id="rel1", source_id="fp1", target_id="dg1", evidence=_cfm_evidence()
            )
        ],
        metadata=metadata,
    )


def _make_csm(**metadata_kwargs):
    import uuid

    from specmetrics.kernel.csm.metadata import BuildMetadata
    from specmetrics.kernel.csm.model import (
        CanonicalSpecificationModel,
        Decision,
        EvidenceRef,
        SpecificationActivity,
    )

    ev = EvidenceRef(graph_node_id="gn", document_id="doc", text="t")
    metadata = BuildMetadata(run_id="csm-run", **metadata_kwargs)
    act_id = str(uuid.uuid4())
    dec_id = str(uuid.uuid4())
    return CanonicalSpecificationModel(
        run_id="csm-run",
        specification_activities={
            act_id: SpecificationActivity(
                id=act_id, activity_type="exploration", description="Explore", evidence_references=[ev]
            ),
        },
        decisions={
            dec_id: Decision(id=dec_id, description="Decide", evidence_references=[ev]),
        },
        metadata=metadata,
    )


def test_entities_for_rule_no_model_returns_empty():
    """Kills _entities_for_rule__mutmut_1/2/6/7/8 (cfm getattr), __mutmut_10 (isinstance)."""
    assert _entities_for_rule(_Ctx()) == []


def test_entities_for_rule_non_cfm_returns_empty():
    """Kills _entities_for_rule__mutmut_10 (isinstance inversion)."""
    assert _entities_for_rule(_Ctx(canonical_model=object())) == []


def test_entities_for_rule_applied_rule_packs():
    """Kills _entities_for_rule__mutmut_11-18 (applied_rules getattr),
    __mutmut_24-32 (rule_pack_id get), __mutmut_33-41 (rule_id get),
    __mutmut_42-50 (rule_type get), __mutmut_51-59 (methodology get),
    __mutmut_60-68 (description get)."""
    cfm = _make_cfm(
        applied_rules=[
            {
                "rule_pack_id": "rp1",
                "rule_id": "r1",
                "rule_type": "exclusion",
                "methodology": "FPA",
                "description": "Exclude EQ",
            },
        ],
        element_counts={"actor": 1, "data_group": 2},
        vaf=1.05,
    )
    entities = _entities_for_rule(_Ctx(canonical_model=cfm))
    assert entities[0] == {
        "type": "applied_rule_pack",
        "rule_pack_id": "rp1",
        "rule_id": "r1",
        "rule_type": "exclusion",
        "methodology": "FPA",
        "description": "Exclude EQ",
    }
    assert entities[1] == {
        "type": "modification_summary",
        "entities_modified": 3,
        "vaf_applied": 1.05,
    }


def test_entities_for_rule_missing_rule_fields_default():
    """Kills _entities_for_rule__mutmut_27/28/29/30/31/32 (rule_pack_id default),
    __mutmut_36/37/38/39/40/41 (rule_id default), etc."""
    cfm = _make_cfm(applied_rules=[{"rule_pack_id": "only-id"}])
    entities = _entities_for_rule(_Ctx(canonical_model=cfm))
    assert entities[0] == {
        "type": "applied_rule_pack",
        "rule_pack_id": "only-id",
        "rule_id": "",
        "rule_type": "",
        "methodology": "",
        "description": "",
    }



def test_entities_for_rule_no_element_counts_defaults_zero():
    """Kills _entities_for_rule element_counts branch defaults."""
    cfm = _make_cfm()  # element_counts defaults to {}
    entities = _entities_for_rule(_Ctx(canonical_model=cfm))
    assert entities[0] == {
        "type": "modification_summary",
        "entities_modified": 0,
        "vaf_applied": None,
    }


def test_entities_for_cfm_no_model_returns_empty():
    """Kills _entities_for_cfm__mutmut_1/2/6/7/8 (cfm getattr), __mutmut_10 (isinstance),
    __mutmut_9 (stage_entities None)."""
    assert _entities_for_cfm(_Ctx()) == []


def test_entities_for_cfm_non_model_returns_empty():
    """Kills _entities_for_cfm__mutmut_10 (isinstance inversion)."""
    assert _entities_for_cfm(_Ctx(canonical_model=object())) == []


def test_entities_for_cfm_builds_category_payloads():
    """Kills _entities_for_cfm__mutmut_11 (category_map None),
    __mutmut_24/25/26/27 (model_dump mode), __mutmut_28/29/30 (type assignment),
    __mutmut_31/41 (append None), __mutmut_32-39 (relationship dump)."""
    entities = _entities_for_cfm(_Ctx(canonical_model=_make_cfm()))
    types = [e["type"] for e in entities]
    assert "actor" in types
    assert "functional_process" in types
    assert "data_group" in types
    assert "relationship" in types
    actor = next(e for e in entities if e["type"] == "actor")
    assert actor["id"] == "a1"
    assert actor["name"] == "User"
    rel = next(e for e in entities if e["type"] == "relationship")
    assert rel["id"] == "rel1"


def test_entities_for_csm_no_model_returns_empty():
    """Kills _entities_for_csm__mutmut_1/2/6/7/8 (csm getattr), __mutmut_10 (isinstance),
    __mutmut_9 (stage_entities None)."""
    assert _entities_for_csm(_Ctx()) == []


def test_entities_for_csm_non_model_returns_empty():
    """Kills _entities_for_csm__mutmut_10 (isinstance inversion)."""
    assert _entities_for_csm(_Ctx(canonical_spec_model=object())) == []


def test_entities_for_csm_builds_category_payloads():
    """Kills _entities_for_csm__mutmut_11 (category_map None),
    __mutmut_30/31/32/33 (model_dump mode), __mutmut_34/35/36 (type assignment),
    __mutmut_37/38/39 (description in), __mutmut_40-45 (description truncate),
    __mutmut_46 (append None)."""
    entities = _entities_for_csm(_Ctx(canonical_spec_model=_make_csm()))
    types = [e["type"] for e in entities]
    assert "specification_activity" in types
    assert "decision" in types
    act = next(e for e in entities if e["type"] == "specification_activity")
    assert act["description"] == "Explore"
    assert act["activity_type"] == "exploration"


def test_entities_for_csm_truncates_long_description():
    """Kills _entities_for_csm__mutmut_40/43/44/45 (description truncate variants)."""
    csm = _make_csm()
    act = next(iter(csm.specification_activities.values()))
    act.description = "x" * 500
    entities = _entities_for_csm(_Ctx(canonical_spec_model=csm))
    payload = next(e for e in entities if e["type"] == "specification_activity")
    assert len(payload["description"]) == 200


def test_entities_for_measure_no_result_returns_all_metric_entries():
    """Kills _entities_for_measure__mutmut_1/2/3/7/8/9 (mr getattr),
    __mutmut_11 (isinstance), __mutmut_10 (stage_entities None),
    __mutmut_51/52 (metric_name_to_cli / list), __mutmut_53-61 (_build_metric_entry args)."""
    entities = _entities_for_measure(_Ctx())
    assert entities == [
        {"metric": "business_complexity_points", "total": 0, "status": "completed", "duration_ms": 0},
        {"metric": "function_points", "total": 0, "status": "completed", "duration_ms": 0},
        {"metric": "simplified_function_points", "total": 0, "status": "completed", "duration_ms": 0},
        {"metric": "snap", "total": 0, "status": "completed", "duration_ms": 0},
        {"metric": "story_points", "total": 0, "status": "completed", "duration_ms": 0},
        {"metric": "tshirt", "total": 0, "status": "completed", "duration_ms": 0},
        {"metric": "token_points", "total": 0, "status": "completed", "duration_ms": 0},
        {"metric": "cognitive_points", "total": 0, "status": "completed", "duration_ms": 0},
    ]


def test_entities_for_measure_with_results():
    """Kills _entities_for_measure metric values flow-through and breakdown branches."""
    mr = {
        "fpa_total_function_points": 10,
        "fpa_breakdown": [{"type": "ILF"}],
        "cognitive_raw_score": 5.55,
        "cognitive_bloom_breakdown": {"L1": {"total": 3.33}},
        "fpa_warnings": [{"message": "w"}],
    }
    entities = _entities_for_measure(_Ctx(measurement_result=mr))
    fp = next(e for e in entities if e["metric"] == "function_points")
    assert fp["total"] == 10
    assert fp["breakdown"] == [{"type": "ILF"}]
    assert fp["warnings"] == ["w"]
    cp = next(e for e in entities if e["metric"] == "cognitive_points")
    assert cp["total"] == 5.5


def test_entities_for_rule_absent_rule_pack_id_default():
    """Kills _entities_for_rule__mutmut_27/29/32 (rule_pack_id default swaps when key absent)."""
    cfm = _make_cfm(applied_rules=[{"rule_id": "r1"}])
    entities = _entities_for_rule(_Ctx(canonical_model=cfm))
    assert entities[0] == {
        "type": "applied_rule_pack",
        "rule_pack_id": "",
        "rule_id": "r1",
        "rule_type": "",
        "methodology": "",
        "description": "",
    }


def test_entities_for_rule_absent_rule_id_default():
    """Kills _entities_for_rule__mutmut_36/38/41 (rule_id default swaps when key absent)."""
    cfm = _make_cfm(applied_rules=[{"rule_pack_id": "rp"}])
    entities = _entities_for_rule(_Ctx(canonical_model=cfm))
    assert entities[0]["rule_id"] == ""
    assert entities[0]["rule_type"] == ""
    assert entities[0]["methodology"] == ""
    assert entities[0]["description"] == ""


def test_entities_for_rule_absent_rule_type_default():
    """Kills _entities_for_rule__mutmut_45/47/50 (rule_type default swaps when key absent)."""
    cfm = _make_cfm(applied_rules=[{"rule_pack_id": "rp", "rule_id": "r1"}])
    entities = _entities_for_rule(_Ctx(canonical_model=cfm))
    assert entities[0]["rule_type"] == ""


def test_entities_for_rule_absent_methodology_default():
    """Kills _entities_for_rule__mutmut_54/56/59 (methodology default swaps when key absent)."""
    cfm = _make_cfm(
        applied_rules=[{"rule_pack_id": "rp", "rule_id": "r1", "rule_type": "x"}]
    )
    entities = _entities_for_rule(_Ctx(canonical_model=cfm))
    assert entities[0]["methodology"] == ""


def test_entities_for_rule_absent_description_default():
    """Kills _entities_for_rule__mutmut_63/65/68 (description default swaps when key absent)."""
    cfm = _make_cfm(
        applied_rules=[{"rule_pack_id": "rp", "rule_id": "r1", "rule_type": "x", "methodology": "m"}]
    )
    entities = _entities_for_rule(_Ctx(canonical_model=cfm))
    assert entities[0]["description"] == ""


def test_entities_for_rule_vaf_applied_default_none():
    """Kills _entities_for_rule__mutmut_90 (vaf_applied getattr default)."""
    cfm = _make_cfm()  # vaf defaults to None
    entities = _entities_for_rule(_Ctx(canonical_model=cfm))
    assert entities[0]["vaf_applied"] is None


def test_entities_for_cfm_relationship_type():
    """Kills _entities_for_cfm__mutmut_36/37/38/39 (relationship type assignment)."""
    entities = _entities_for_cfm(_Ctx(canonical_model=_make_cfm()))
    rel = next(e for e in entities if e["id"] == "rel1")
    assert rel["type"] == "relationship"
