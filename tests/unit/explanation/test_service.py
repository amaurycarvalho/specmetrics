from __future__ import annotations


from specmetrics.kernel.explanation.service import (
    _build_metrics_from_elements,
    _build_metrics_from_measurement_result,
    ExplainService,
    ExplanationConfig,
)


def _make_cfm():
    from specmetrics.kernel.cfm.model import CanonicalFunctionalModel, Actor, BuildMetadata, EvidenceRef

    return CanonicalFunctionalModel(
        run_id="test-run",
        actors={
            "a1": Actor(id="a1", name="User", evidence=EvidenceRef(graph_node_id="n1", document_id="doc1", text="evidence")),
        },
        functional_processes={},
        business_rules={},
        data_groups={},
        relationships=[],
        operations={},
        unclassified={},
        metadata=BuildMetadata(
            run_id="test-run",
            build_duration_ms=10,
            element_counts={"actors": 1},
            total_input_nodes=1,
            unclassified_count=0,
        ),
    )


class TestBuildMetricsFromElements:
    def test_empty_elements_returns_zero_count(self):
        metrics = _build_metrics_from_elements([], [], None)
        assert len(metrics) == 1
        assert metrics[0].metric_name == "function_count"
        assert metrics[0].metric_value == 0

    def test_elements_produce_function_count(self):
        elements = [{"element_id": "e1", "element_type": "ILF", "element_label": "E1",
                     "complexity": None, "weight": None, "evidence": [], "applied_rules": []}]
        metrics = _build_metrics_from_elements(elements, [], None)
        names = [m.metric_name for m in metrics]
        assert "function_count" in names
        assert "ILF_count" in names


class TestBuildMetricsFromMeasurementResult:
    def test_total_function_points_creates_functional_size(self):
        result = {"total_function_points": 15, "breakdown": {}, "complexity_distribution": []}
        metrics = _build_metrics_from_measurement_result(result, [], [])
        names = [m.metric_name for m in metrics]
        assert "functional_size" in names
        assert metrics[0].metric_value == 15

    def test_breakdown_creates_per_type_metrics(self):
        result = {
            "total_function_points": 10,
            "breakdown": {"ILF": {"count": 2, "total_ufp": 6}, "EIF": {"count": 1, "total_ufp": 4}},
            "complexity_distribution": [],
        }
        metrics = _build_metrics_from_measurement_result(result, [], [])
        names = [m.metric_name for m in metrics]
        assert "ILF_count" in names
        assert "EIF_count" in names

    def test_complexity_distribution(self):
        result = {
            "total_function_points": 0,
            "breakdown": {},
            "complexity_distribution": [
                {"function_type": "ILF", "complexity": "Low", "count": 2, "total_ufp": 6},
            ],
        }
        metrics = _build_metrics_from_measurement_result(result, [], [])
        names = [m.metric_name for m in metrics]
        assert "ILF_Low_count" in names


class TestExplainService:
    def test_explain_without_cfm_or_graph_returns_basic_explanation(self):
        service = ExplainService()
        explanation = service.explain("run-1")
        assert explanation.run_id == "run-1"
        assert len(explanation.metrics) == 1
        assert explanation.metrics[0].metric_value == 0

    def test_explain_with_cfm_produces_elements(self):
        service = ExplainService()
        cfm = _make_cfm()
        explanation = service.explain("run-2", cfm=cfm)
        assert explanation.metrics[0].metric_value >= 1

    def test_explain_with_measurement_result_creates_real_metrics(self):
        service = ExplainService()
        measurement = {"total_function_points": 12, "breakdown": {"ILF": {"count": 3, "total_ufp": 9}}, "complexity_distribution": []}
        explanation = service.explain("run-3", measurement_result=measurement)
        assert explanation.metrics[0].metric_name == "functional_size"
        assert explanation.metrics[0].metric_value == 12

    def test_explain_metric_name_filter(self):
        service = ExplainService()
        measurement = {"total_function_points": 5, "breakdown": {}, "complexity_distribution": []}
        explanation = service.explain("run-4", metric_name="functional_size", measurement_result=measurement)
        assert len(explanation.metrics) == 1
        assert explanation.metrics[0].metric_name == "functional_size"

    def test_explain_metric_not_found_raises(self):
        import pytest
        service = ExplainService()
        with pytest.raises(ValueError, match="not found"):
            service.explain("run-5", metric_name="nonexistent")

    def test_explain_saves_to_disk(self, tmp_path):
        config = ExplanationConfig(storage_dir=str(tmp_path))
        service = ExplainService(config=config)
        service.explain("run-disk")
        saved_file = tmp_path / "run-disk.json"
        assert saved_file.exists()

    def test_load_explanation_from_disk(self, tmp_path):
        config = ExplanationConfig(storage_dir=str(tmp_path))
        service = ExplainService(config=config)
        service.explain("run-load", measurement_result={"total_function_points": 7, "breakdown": {}, "complexity_distribution": []})
        service2 = ExplainService(config=config)
        loaded = service2.load_explanation("run-load")
        assert loaded is not None
        assert loaded.run_id == "run-load"
        assert loaded.metrics[0].metric_value == 7

    def test_compare_missing_both_returns_graceful(self):
        service = ExplainService()
        result = service.compare("missing-a", "missing-b")
        assert "not found" in result.summary.lower()

    def test_compare_missing_baseline_returns_graceful(self):
        service = ExplainService()
        service.explain("exists")
        result = service.compare("missing", "exists")
        assert "not found" in result.summary.lower()

    def test_compare_with_spec_path_uses_provided_path(self):
        service = ExplainService()
        explanation = service.explain("spec-path-test", spec_path="specs/my-feature/spec.md")
        assert explanation.spec_path == "specs/my-feature/spec.md"
