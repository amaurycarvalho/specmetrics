from pathlib import Path

import pytest

from specmetrics.kernel.engine_rule import RulePackLoader


@pytest.fixture
def rules_dir(tmp_path: Path) -> Path:
    d = tmp_path / "rules"
    d.mkdir(parents=True)
    return d


def test_load_meta_with_version(rules_dir: Path):
    path = rules_dir / "test_rules.yaml"
    path.write_text(
        "version: '1.0.0'\n"
        "framework: speckit\n"
        "document_types:\n"
        "  - specification\n"
        "description: Test pack\n"
        "rules: []\n"
    )
    meta = RulePackLoader.load_meta(path)
    assert meta.version == "1.0.0"
    assert meta.framework == "speckit"
    assert meta.document_types == ["specification"]
    assert meta.description == "Test pack"


def test_load_meta_no_version(rules_dir: Path):
    path = rules_dir / "test_rules.yaml"
    path.write_text("rules: []\n")
    meta = RulePackLoader.load_meta(path)
    assert meta.version == ""
    assert meta.document_types == []


def test_load_rules_old_format(rules_dir: Path):
    path = rules_dir / "old_rules.yaml"
    path.write_text(
        "rules:\n"
        "  - id: test-rule\n"
        "    name: Test Rule\n"
        "    pattern:\n"
        "      heading: Test\n"
        "    type: entity\n"
        "    confidence: 0.95\n"
        "    priority: 80\n"
    )
    rules = RulePackLoader.load(path)
    assert len(rules) == 1
    assert rules[0].id == "test-rule"
    assert rules[0].type == "entity"
    assert rules[0].confidence == 0.95
    assert rules[0].priority == 80
    assert rules[0].pattern == {"heading": "Test"}


def test_load_rules_new_format_regex(rules_dir: Path):
    path = rules_dir / "new_rules.yaml"
    path.write_text(
        "version: '1.0.0'\n"
        "framework: speckit\n"
        "rules:\n"
        "  - rule_id: speckit-user-story\n"
        "    pattern: '^### User Story \\d+'\n"
        "    semantic_type: entity\n"
        "    confidence: 0.95\n"
        "    priority: 80\n"
        "    target_sections:\n"
        "      - User Scenarios\n"
        "    capture_groups:\n"
        "      story_number: 1\n"
        "    document_type: specification\n"
    )
    rules = RulePackLoader.load(path)
    assert len(rules) == 1
    assert rules[0].id == "speckit-user-story"
    assert rules[0].type == "entity"
    assert rules[0].pattern == {"regex": "^### User Story \\d+"}
    assert rules[0].target_sections == ["User Scenarios"]
    assert rules[0].capture_groups == {"story_number": 1}
    assert rules[0].document_type == "specification"


def test_load_rules_invalid_rule_skipped(rules_dir: Path):
    path = rules_dir / "invalid_rules.yaml"
    path.write_text(
        "rules:\n"
        "  - id: valid-rule\n"
        "    name: Valid\n"
        "    pattern:\n"
        "      heading: Test\n"
        "    type: entity\n"
        "    confidence: 0.9\n"
        "    priority: 50\n"
        "  - id: ''\n"
        "    name: Invalid\n"
        "    pattern:\n"
        "      heading: Bad\n"
        "    type: entity\n"
        "    confidence: 0.9\n"
        "    priority: 50\n"
    )
    rules = RulePackLoader.load(path)
    assert len(rules) == 1
    assert rules[0].id == "valid-rule"


def test_validate_version_valid():
    assert RulePackLoader.validate_version("1.0.0")
    assert RulePackLoader.validate_version("0.0.1")
    assert RulePackLoader.validate_version("2.3.4")
    assert RulePackLoader.validate_version("10.99.100")


def test_validate_version_invalid():
    assert not RulePackLoader.validate_version("1.0")
    assert not RulePackLoader.validate_version("1.0.0.0")
    assert not RulePackLoader.validate_version("abc")
    assert not RulePackLoader.validate_version("")
    assert not RulePackLoader.validate_version("v1.0.0")
    assert not RulePackLoader.validate_version("1.0.0-beta")


def test_rule_pack_not_found(tmp_path: Path):
    path = tmp_path / "nonexistent.yaml"
    with pytest.raises(FileNotFoundError):
        RulePackLoader.load(path)


def test_rule_pack_empty_rules(rules_dir: Path):
    path = rules_dir / "empty.yaml"
    path.write_text("rules: []\n")
    rules = RulePackLoader.load(path)
    assert rules == []
