from __future__ import annotations

from specmetrics.kernel.explanation.models import MeasurementExplanation
from specmetrics.kernel.explanation.service import ExplainService


class TestExplainServiceIntegration:
    def test_explain_with_cfm_and_graph_and_measurement(self):
        from specmetrics.kernel.cfm.model import CanonicalFunctionalModel, Actor, BuildMetadata, EvidenceRef
        from specmetrics.kernel.evidence_graph import EvidenceGraph, GraphMetadata, GraphNode

        cfm = CanonicalFunctionalModel(
            run_id="int-test",
            actors={"a1": Actor(id="a1", name="User", evidence=EvidenceRef(graph_node_id="n1", document_id="doc1", text="evidence"))},
            functional_processes={}, business_rules={}, data_groups={},
            relationships=[], operations={}, unclassified={},
            metadata=BuildMetadata(
                run_id="int-test", build_duration_ms=0, element_counts={"actors": 1},
                total_input_nodes=1, unclassified_count=0,
            ),
        )
        graph = EvidenceGraph(
            run_id="int-test",
            nodes={
                "n1": GraphNode(
                    id="n1", node_type="extracted_element", semantic_type="fact",
                    document_id="spec.md", section_id="Actors", text="User", element_id="a1",
                ),
            },
            edges=[],
            metadata=GraphMetadata(run_id="int-test", node_count=1, edge_count=0, documents_covered=["spec.md"]),
        )
        measurement = {
            "total_function_points": 5,
            "breakdown": {"ILF": {"count": 1, "total_ufp": 3}, "EIF": {"count": 1, "total_ufp": 2}},
            "complexity_distribution": [],
        }

        service = ExplainService()
        explanation = service.explain("int-test", cfm=cfm, graph=graph, measurement_result=measurement, spec_path="specs/test/spec.md")

        assert isinstance(explanation, MeasurementExplanation)
        assert explanation.run_id == "int-test"
        assert explanation.spec_path == "specs/test/spec.md"
        assert len(explanation.metrics) > 0

        metric_names = [m.metric_name for m in explanation.metrics]
        assert "functional_size" in metric_names
        assert "ILF_count" in metric_names
        assert "EIF_count" in metric_names

        fs_metric = next(m for m in explanation.metrics if m.metric_name == "functional_size")
        assert fs_metric.metric_value == 5

    def test_compare_with_persisted_explanations(self, tmp_path):
        from specmetrics.kernel.explanation.service import ExplanationConfig

        config = ExplanationConfig(storage_dir=str(tmp_path))
        service = ExplainService(config=config)

        service.explain("base", measurement_result={"total_function_points": 10, "breakdown": {}, "complexity_distribution": []})
        service.explain("comp", measurement_result={"total_function_points": 12, "breakdown": {}, "complexity_distribution": []})

        service2 = ExplainService(config=config)
        comparison = service2.compare("base", "comp")
        assert comparison.baseline_run_id == "base"
        assert comparison.comparison_run_id == "comp"
        assert len(comparison.changed_metrics) == 1
        assert comparison.changed_metrics[0].delta == 2
