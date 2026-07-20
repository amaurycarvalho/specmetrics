from __future__ import annotations

_TRUNCATE_TEXT_LENGTH = 200


def _truncate_text(text: str | None, max_len: int = _TRUNCATE_TEXT_LENGTH) -> str | None:
    if text is None:
        return None
    return text[:max_len] if len(text) > max_len else text


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


def test_truncate_text_short():
    text = "short text"
    assert _truncate_text(text, 50) == text


def test_truncate_text_long():
    text = "a" * 300
    result = _truncate_text(text, 200)
    assert len(result) == 200
    assert result == "a" * 200


def test_truncate_text_none():
    assert _truncate_text(None) is None


def test_truncate_text_exact():
    text = "a" * 200
    assert _truncate_text(text, 200) == text


def test_truncate_entities_no_truncation():
    entities = [{"id": str(i)} for i in range(50)]
    result = _truncate_entities(entities, 100)
    assert len(result) == 50
    assert all("_truncated" not in e for e in result)


def test_truncate_entities_first_n():
    entities = [{"id": str(i)} for i in range(100)]
    result = _truncate_entities(entities, 10)
    assert len(result) == 11
    assert result[-1] == {"_truncated": True, "_total_count": 100}
    assert result[0]["id"] == "0"
    assert result[9]["id"] == "9"


def test_truncate_entities_per_category():
    entities = []
    for i in range(30):
        entities.append({"id": str(i), "type": "decision"})
    for i in range(30, 60):
        entities.append({"id": str(i), "type": "constraint"})
    result = _truncate_entities(entities, 10, per_category=True)
    decisions = [e for e in result if e.get("type") == "decision"]
    constraints = [e for e in result if e.get("type") == "constraint"]
    summary = [e for e in result if "_truncated" in e]
    assert len(decisions) == 10
    assert len(constraints) == 10
    assert len(summary) == 1
    assert summary[0] == {"_truncated": True, "_total_count": 60}


def test_truncate_entities_per_category_no_truncation():
    entities = [{"id": str(i), "type": "decision"} for i in range(5)]
    result = _truncate_entities(entities, 10, per_category=True)
    assert len(result) == 5
    assert all("_truncated" not in e for e in result)


def test_truncate_entities_empty():
    assert _truncate_entities([], 100) == []


def test_truncate_entities_single_category_at_limit():
    entities = [{"id": str(i), "type": "test"} for i in range(10)]
    result = _truncate_entities(entities, 10, per_category=True)
    assert len(result) == 10
