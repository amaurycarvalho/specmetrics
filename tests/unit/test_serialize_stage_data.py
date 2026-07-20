from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MockStageOutputItem:
    name: str
    count: int = 0
    count_type: str = "items"
    duration_ms: int = 0


@dataclass
class MockPipelineResult:
    stage_details: list[MockStageOutputItem]
    stage_entities: dict[str, list[dict]] = field(default_factory=dict)
    metric_results: list[Any] = field(default_factory=list)


_TRUNCATE_TEXT_LENGTH = 200


def _truncate_entities(
    entities: list[dict],
    max_per_stage: int,
    per_category: bool = False,
) -> list[dict]:
    if len(entities) <= max_per_stage:
        return entities
    if per_category:
        truncated: list[dict] = []
        categories: dict[str, list[dict]] = {}
        for e in entities:
            cat = e.get("type", "_other")
            categories.setdefault(cat, []).append(e)
        for cat_list in categories.values():
            truncated.extend(cat_list[:max_per_stage])
        truncated.append({"_truncated": True, "_total_count": len(entities)})
        return truncated
    truncated = entities[:max_per_stage]
    truncated.append({"_truncated": True, "_total_count": len(entities)})
    return truncated


def _serialize_stage_data(
    result: MockPipelineResult,
    max_entities_per_stage: int = 5000,
) -> dict[str, list[dict]]:
    csm_cfm_stages = {"csm", "cfm"}
    stages: dict[str, list[dict]] = {}
    for sd in result.stage_details:
        entry: dict = {
            "name": sd.name,
            "count": sd.count,
            "count_type": sd.count_type,
            "duration_ms": sd.duration_ms,
        }
        raw_entities = result.stage_entities.get(sd.name, [])
        if raw_entities:
            per_category = sd.name in csm_cfm_stages
            entry["entities"] = _truncate_entities(raw_entities, max_entities_per_stage, per_category=per_category)
        else:
            entry["entities"] = []
        stages[sd.name] = [entry]
    return stages


def test_empty_entities_backward_compat():
    result = MockPipelineResult(
        stage_details=[MockStageOutputItem(name="discover", count=5, count_type="documents")],
    )
    serialized = _serialize_stage_data(result)
    entry = serialized["discover"][0]
    assert entry["name"] == "discover"
    assert entry["count"] == 5
    assert entry["entities"] == []


def test_populated_entities():
    result = MockPipelineResult(
        stage_details=[MockStageOutputItem(name="discover", count=2, count_type="documents")],
        stage_entities={
            "discover": [
                {"id": "1", "document_type": "sdd", "path": "doc1.sdd"},
                {"id": "2", "document_type": "openspec", "path": "doc2.yaml"},
            ],
        },
    )
    serialized = _serialize_stage_data(result)
    entry = serialized["discover"][0]
    assert len(entry["entities"]) == 2
    assert entry["entities"][0]["document_type"] == "sdd"


def test_truncation_applied():
    entities = [{"id": str(i)} for i in range(100)]
    result = MockPipelineResult(
        stage_details=[MockStageOutputItem(name="extract", count=100, count_type="items")],
        stage_entities={"extract": entities},
    )
    serialized = _serialize_stage_data(result, max_entities_per_stage=10)
    entry = serialized["extract"][0]
    assert len(entry["entities"]) == 11
    assert entry["entities"][-1]["_truncated"] is True


def test_missing_stage_in_entities():
    result = MockPipelineResult(
        stage_details=[MockStageOutputItem(name="cfm", count=50, count_type="items")],
    )
    serialized = _serialize_stage_data(result)
    entry = serialized["cfm"][0]
    assert entry["entities"] == []


def test_top_level_keys_preserved():
    result = MockPipelineResult(
        stage_details=[MockStageOutputItem(name="measure", count=3, count_type="metrics")],
        stage_entities={"measure": [{"metric": "fpa", "total": 10}]},
    )
    serialized = _serialize_stage_data(result)
    entry = serialized["measure"][0]
    assert list(entry.keys()) == ["name", "count", "count_type", "duration_ms", "entities"]


def test_multiple_stages():
    result = MockPipelineResult(
        stage_details=[
            MockStageOutputItem(name="discover", count=2),
            MockStageOutputItem(name="extract", count=5),
        ],
        stage_entities={
            "discover": [{"id": "1"}],
            "extract": [{"id": "a"}, {"id": "b"}],
        },
    )
    serialized = _serialize_stage_data(result)
    assert len(serialized["discover"][0]["entities"]) == 1
    assert len(serialized["extract"][0]["entities"]) == 2
