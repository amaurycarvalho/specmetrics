from __future__ import annotations

from pathlib import Path

import pytest

from specmetrics.kernel.engine_rule import ExtractionRule, RulePackLoader


class TestRulePackLoader:
    def test_load_valid_yaml(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "rules.yaml"
        yaml_file.write_text("""rules:
  - id: "test-rule"
    name: "Test"
    pattern:
      keywords: ["Hello"]
    type: "fact"
    confidence: 0.8
    priority: 50
""")
        rules = RulePackLoader.load(str(yaml_file))
        assert len(rules) == 1
        assert rules[0].id == "test-rule"
        assert rules[0].type == "fact"
        assert rules[0].confidence == 0.8
        assert rules[0].priority == 50

    def test_load_multiple_rules(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "multi.yaml"
        yaml_file.write_text("""rules:
  - id: "rule-1"
    name: "Rule 1"
    pattern:
      keywords: ["One"]
    type: "fact"
    confidence: 0.7
    priority: 50
  - id: "rule-2"
    name: "Rule 2"
    pattern:
      heading: "Test"
    type: "entity"
    confidence: 0.9
    priority: 80
""")
        rules = RulePackLoader.load(str(yaml_file))
        assert len(rules) == 2

    def test_skip_invalid_rule_missing_id(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "bad.yaml"
        yaml_file.write_text("""rules:
  - name: "No ID"
    pattern:
      keywords: ["X"]
    type: "fact"
    confidence: 0.5
    priority: 50
  - id: "valid"
    name: "Valid"
    pattern:
      keywords: ["Y"]
    type: "fact"
    confidence: 0.5
    priority: 50
""")
        rules = RulePackLoader.load(str(yaml_file))
        assert len(rules) == 1
        assert rules[0].id == "valid"

    def test_skip_invalid_type(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "bad_type.yaml"
        yaml_file.write_text("""rules:
  - id: "bad"
    name: "Bad"
    pattern:
      keywords: ["X"]
    type: "invalid_type"
    confidence: 0.5
    priority: 50
""")
        rules = RulePackLoader.load(str(yaml_file))
        assert len(rules) == 0

    def test_skip_invalid_confidence(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "bad_conf.yaml"
        yaml_file.write_text("""rules:
  - id: "bad"
    name: "Bad"
    pattern:
      keywords: ["X"]
    type: "fact"
    confidence: 1.5
    priority: 50
""")
        rules = RulePackLoader.load(str(yaml_file))
        assert len(rules) == 0

    def test_skip_invalid_priority(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "bad_pri.yaml"
        yaml_file.write_text("""rules:
  - id: "bad"
    name: "Bad"
    pattern:
      keywords: ["X"]
    type: "fact"
    confidence: 0.5
    priority: 0
""")
        rules = RulePackLoader.load(str(yaml_file))
        assert len(rules) == 0

    def test_missing_file_raises_error(self) -> None:
        with pytest.raises(FileNotFoundError):
            RulePackLoader.load("/nonexistent/path.yaml")

    def test_empty_rules_list(self, tmp_path: Path) -> None:
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("rules: []")
        rules = RulePackLoader.load(str(yaml_file))
        assert len(rules) == 0


class TestRuleMatching:
    def test_match_rules_by_heading(self) -> None:
        from specmetrics.kernel.engine_rule import RulePackLoader

        rules = [
            ExtractionRule(
                id="actors",
                name="Actors",
                pattern={"heading": "Actors"},
                type="entity",
                confidence=1.0,
                priority=90,
            ),
        ]
        matched = RulePackLoader.match_rules(rules, "Actors", "")
        assert matched is not None
        assert matched.id == "actors"

    def test_match_rules_by_keywords(self) -> None:
        from specmetrics.kernel.engine_rule import RulePackLoader

        rules = [
            ExtractionRule(
                id="user-story",
                name="User Story",
                pattern={"keywords": ["As a", "I want"], "min_matches": 2},
                type="entity",
                confidence=0.95,
                priority=80,
            ),
        ]
        matched = RulePackLoader.match_rules(rules, "", "As a user, I want to login")
        assert matched is not None
        assert matched.id == "user-story"

    def test_higher_priority_wins(self) -> None:
        from specmetrics.kernel.engine_rule import RulePackLoader

        rules = [
            ExtractionRule(
                id="low-pri",
                name="Low",
                pattern={"heading": "Actors"},
                type="entity",
                confidence=0.8,
                priority=50,
            ),
            ExtractionRule(
                id="high-pri",
                name="High",
                pattern={"heading": "Actors"},
                type="entity",
                confidence=1.0,
                priority=90,
            ),
        ]
        matched = RulePackLoader.match_rules(rules, "Actors", "")
        assert matched is not None
        assert matched.id == "high-pri"

    def test_no_match_returns_none(self) -> None:
        from specmetrics.kernel.engine_rule import RulePackLoader

        rules = [
            ExtractionRule(
                id="actors",
                name="Actors",
                pattern={"heading": "Actors"},
                type="entity",
                confidence=1.0,
                priority=90,
            ),
        ]
        matched = RulePackLoader.match_rules(rules, "Constraints", "")
        assert matched is None
