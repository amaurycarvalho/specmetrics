from __future__ import annotations

import pytest

from specmetrics.kernel.cfm.classifier import classify_node, strip_framework_labels
from specmetrics.kernel.evidence_graph import GraphNode


class TestClassifyNode:
    def test_classify_fact_as_business_rule(self) -> None:
        node = GraphNode(
            id="n1", node_type="extracted_element", semantic_type="fact",
            document_id="doc1", text="System must validate email addresses",
        )
        result = classify_node(node)
        assert result == "business_rule"

    def test_classify_entity_as_actor(self) -> None:
        node = GraphNode(
            id="n2", node_type="extracted_element", semantic_type="entity",
            document_id="doc1", text="Administrator",
        )
        result = classify_node(node)
        assert result == "actor"

    def test_classify_entity_as_data_group(self) -> None:
        node = GraphNode(
            id="n3", node_type="extracted_element", semantic_type="entity",
            document_id="doc1", text="UserAccount",
        )
        result = classify_node(node)
        assert result == "data_group"

    def test_classify_relationship_direct(self) -> None:
        node = GraphNode(
            id="n4", node_type="extracted_element", semantic_type="relationship",
            document_id="doc1", text="User creates Account",
        )
        result = classify_node(node)
        assert result == "relationship"

    def test_classify_operation_direct(self) -> None:
        node = GraphNode(
            id="n5", node_type="extracted_element", semantic_type="operation",
            document_id="doc1", text="Send notification email",
        )
        result = classify_node(node)
        assert result == "operation"

    def test_classify_evidence_node(self) -> None:
        node = GraphNode(
            id="n6", node_type="evidence",
            document_id="doc1", text="Some evidence text",
        )
        result = classify_node(node)
        assert result is None

    def test_classify_missing_semantic_type(self) -> None:
        node = GraphNode(
            id="n7", node_type="extracted_element", semantic_type=None,
            document_id="doc1", text="Something",
        )
        result = classify_node(node)
        assert result is None


class TestStripFrameworkLabels:
    def test_strip_openspec_label(self) -> None:
        assert strip_framework_labels("OpenSpec Section: Login") == "Login"

    def test_strip_speckit_label(self) -> None:
        assert strip_framework_labels("SpecKit Document: API Spec") == "API Spec"

    def test_strip_specmetrics_label(self) -> None:
        assert strip_framework_labels("SpecMetrics Measurement: FP") == "FP"

    def test_preserve_clean_name(self) -> None:
        assert strip_framework_labels("User Registration") == "User Registration"

    def test_strip_case_insensitive(self) -> None:
        assert strip_framework_labels("openspec section: login") == "login"

    def test_strip_prefix_in_middle(self) -> None:
        assert strip_framework_labels("Login - OpenSpec Section") == "Login - OpenSpec Section"
