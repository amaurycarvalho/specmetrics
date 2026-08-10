from __future__ import annotations

from types import SimpleNamespace

from specmetrics.plugins.measurement.cognitive_points._evidence import (
    cfm_evidence,
    csm_evidence,
    extract_content_text_cfm,
    extract_content_text_csm,
)


class TestCsmEvidence:
    def test_empty_returns_none(self):
        assert csm_evidence([]) is None

    def test_first_reference_used(self):
        refs = [
            SimpleNamespace(
                graph_node_id="g1", document_id="d1", section_id="s1", text="t1"
            ),
            SimpleNamespace(
                graph_node_id="g2", document_id="d2", section_id="s2", text="t2"
            ),
        ]
        result = csm_evidence(refs)
        assert result is not None
        assert result.graph_node_id == "g1"
        assert result.document_id == "d1"
        assert result.section_id == "s1"
        assert result.text == "t1"

    def test_missing_attributes_defaults(self):
        refs = [SimpleNamespace(graph_node_id="g")]
        result = csm_evidence(refs)
        assert result is not None
        assert result.graph_node_id == "g"
        assert result.document_id == ""
        assert result.section_id is None
        assert result.text == ""


class TestCfmEvidence:
    def test_none_returns_none(self):
        assert cfm_evidence(None) is None

    def test_present_returns_evidence(self):
        ev = SimpleNamespace(
            graph_node_id="g", document_id="d", section_id="s", text="t"
        )
        result = cfm_evidence(ev)
        assert result is not None
        assert result.graph_node_id == "g"
        assert result.document_id == "d"
        assert result.section_id == "s"
        assert result.text == "t"

    def test_missing_attributes_defaults(self):
        result = cfm_evidence(SimpleNamespace(graph_node_id="x"))
        assert result is not None
        assert result.graph_node_id == "x"
        assert result.document_id == ""
        assert result.section_id is None
        assert result.text == ""


class TestExtractContentTextCsm:
    def test_name_and_description(self):
        elem = SimpleNamespace(name="Alpha", description="Beta")
        assert extract_content_text_csm(elem) == "Alpha Beta"

    def test_only_name(self):
        assert extract_content_text_csm(SimpleNamespace(name="Solo")) == "Solo"

    def test_missing_attributes(self):
        assert extract_content_text_csm(SimpleNamespace()) == ""


class TestExtractContentTextCfm:
    def test_relationship_uses_name_only(self):
        elem = SimpleNamespace(name="Rel", description="Should be ignored")
        assert extract_content_text_cfm(elem, "relationships") == "Rel"

    def test_non_relationship_uses_name_and_description(self):
        elem = SimpleNamespace(name="Proc", description="Does work")
        assert extract_content_text_cfm(elem, "operations") == "Proc Does work"

    def test_missing_attributes(self):
        assert extract_content_text_cfm(SimpleNamespace(), "operations") == ""