from __future__ import annotations

import json

from specmetrics.cli.output_models import (
    ErrorRecord,
    MeasureMetadata,
    MeasureOutput,
    MetricResult,
    StageInfo,
)


class TestMeasureOutputSchema:
    def test_minimal_output_serializes(self):
        output = MeasureOutput(
            measure=MeasureMetadata(
                sdd_framework="speckit",
                created="2026-07-20T10:00:00Z",
                llm={"provider": "test", "model": "test-model"},
                project_path="/tmp/test",
            ),
            results=[
                MetricResult(name="function_points", total=42),
            ],
            stages=[
                StageInfo(name="discover", count=5, count_type="documents"),
            ],
            errors=[],
        )
        data = json.loads(output.model_dump_json())
        assert data["measure"]["sdd_framework"] == "speckit"
        assert len(data["results"]) == 1
        assert data["results"][0]["name"] == "function_points"
        assert data["results"][0]["total"] == 42
        assert data["errors"] == []

    def test_output_with_failed_metrics(self):
        output = MeasureOutput(
            measure=MeasureMetadata(
                sdd_framework="openspec",
                created="2026-07-20T10:00:00Z",
                llm={"provider": "", "model": ""},
                project_path="/tmp/test",
            ),
            results=[
                MetricResult(name="function_points", total=42, status="completed"),
                MetricResult(name="business_complexity_points", total=0, status="failed"),
            ],
            stages=[],
            errors=[
                ErrorRecord(
                    stage="measure",
                    message="BCP measurement failed: LLM timeout",
                    details={"metric": "bcp"},
                ),
            ],
        )
        data = json.loads(output.model_dump_json())
        assert len(data["results"]) == 2
        assert data["results"][1]["status"] == "failed"
        assert len(data["errors"]) == 1
        assert "LLM timeout" in data["errors"][0]["message"]

    def test_output_serializes_all_metric_results(self):
        metric_names = [
            "function_points",
            "business_complexity_points",
            "simplified_function_points",
            "snap",
            "story_points",
            "tshirt",
            "token_points",
            "cognitive_points",
        ]
        output = MeasureOutput(
            measure=MeasureMetadata(
                sdd_framework="speckit",
                created="2026-07-20T10:00:00Z",
                llm={"provider": "test", "model": "test"},
                project_path="/tmp/test",
            ),
            results=[MetricResult(name=n, total=i) for i, n in enumerate(metric_names)],
            stages=[],
            errors=[],
        )
        data = json.loads(output.model_dump_json())
        assert len(data["results"]) == 8

    def test_output_includes_measure_id_before_sdd_framework(self):
        output = MeasureOutput(
            measure=MeasureMetadata(
                id="20260720-143022-a1b2c3d4",
                id_path="20260720-143022-a1b2c3d4",
                sdd_framework="speckit",
                created="2026-07-20T10:00:00Z",
                llm={"provider": "test"},
                project_path="/tmp/test",
            ),
            results=[],
            stages=[],
            errors=[],
        )
        data = json.loads(output.model_dump_json())
        keys = list(data["measure"].keys())
        id_idx = keys.index("id")
        sdd_idx = keys.index("sdd_framework")
        assert id_idx < sdd_idx, "measure.id must appear before measure.sdd_framework"
        assert data["measure"]["id"] == "20260720-143022-a1b2c3d4"
        assert data["measure"]["id_path"] == "20260720-143022-a1b2c3d4"

    def test_output_requires_measure_metadata(self):
        try:
            MeasureOutput(
                results=[],
                stages=[],
                errors=[],
            )
            assert False, "Should have raised ValidationError"
        except Exception:
            pass
