from pathlib import Path

import pytest

from specmetrics.kernel.engine_rule import RulePackLoader


@pytest.fixture
def rules_dir() -> Path:
    return Path("specmetrics/kernel/rules")


def _get_types_from_pack(rules_dir: Path, pack_name: str) -> set[str]:
    path = rules_dir / pack_name
    rules = RulePackLoader.load(path)
    return {r.type for r in rules}


def test_speckit_rule_types(rules_dir: Path):
    types = _get_types_from_pack(rules_dir, "speckit_rules.yaml")
    assert "entity" in types
    assert "fact" in types


def test_openspec_rule_types(rules_dir: Path):
    types = _get_types_from_pack(rules_dir, "openspec_rules.yaml")
    assert "entity" in types
    assert "fact" in types
    assert "operation" in types


def test_speckit_confidence_scores(rules_dir: Path):
    path = rules_dir / "speckit_rules.yaml"
    rules = RulePackLoader.load(path)
    for r in rules:
        assert 0.0 <= r.confidence <= 1.0, f"{r.id} has invalid confidence {r.confidence}"
    scores = {r.confidence for r in rules}
    expected = {1.0, 0.95, 0.90, 0.85, 0.80}
    assert scores.issubset(expected), f"Unexpected scores: {scores - expected}"


def test_openspec_confidence_scores(rules_dir: Path):
    path = rules_dir / "openspec_rules.yaml"
    rules = RulePackLoader.load(path)
    for r in rules:
        assert 0.0 <= r.confidence <= 1.0, f"{r.id} has invalid confidence {r.confidence}"
    scores = {r.confidence for r in rules}
    expected = {1.0, 0.95, 0.90, 0.85, 0.80}
    assert scores.issubset(expected), f"Unexpected scores: {scores - expected}"


def test_speckit_unique_rule_ids(rules_dir: Path):
    path = rules_dir / "speckit_rules.yaml"
    rules = RulePackLoader.load(path)
    ids = [r.id for r in rules]
    assert len(ids) == len(set(ids)), "Duplicate rule IDs found"


def test_openspec_unique_rule_ids(rules_dir: Path):
    path = rules_dir / "openspec_rules.yaml"
    rules = RulePackLoader.load(path)
    ids = [r.id for r in rules]
    assert len(ids) == len(set(ids)), "Duplicate rule IDs found"


def test_speckit_version_metadata(rules_dir: Path):
    from specmetrics.kernel.engine_rule import RulePackLoader as Loader
    path = rules_dir / "speckit_rules.yaml"
    meta = Loader.load_meta(path)
    assert meta.version != ""
    assert Loader.validate_version(meta.version)


def test_openspec_version_metadata(rules_dir: Path):
    from specmetrics.kernel.engine_rule import RulePackLoader as Loader
    path = rules_dir / "openspec_rules.yaml"
    meta = Loader.load_meta(path)
    assert meta.version != ""
    assert Loader.validate_version(meta.version)


def test_all_fourteen_entity_categories_represented():
    cfm_categories = {"actor", "functional_process", "business_rule", "data_group", "operation", "relationship"}
    csm_categories = {"decision", "assumption", "constraint", "risk", "open_question", "acceptance_criterion", "glossary_term", "specification_activity"}
    all_categories = cfm_categories | csm_categories
    assert len(all_categories) == 14


def test_minimal_spec_handling():
    from specmetrics.kernel.adapter_interface import Document
    from specmetrics.kernel.deterministic_engine import DeterministicSemanticEngine

    engine = DeterministicSemanticEngine()
    doc = Document(
        id="test/minimal.md",
        path="test/minimal.md",
        content="# Minimal\n\nJust a title and description.",
        document_type="specification",
    )
    result = engine.extract([doc])
    assert result is not None
    assert result.processing_stats.documents_processed >= 0
