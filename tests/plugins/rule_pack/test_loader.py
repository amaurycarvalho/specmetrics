from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from specmetrics.plugins.rule_pack.loader import RulePackLoader


@pytest.fixture
def loader(tmp_path: Path) -> RulePackLoader:
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    return RulePackLoader(str(rules_dir))


def _write_rule_pack(rules_dir: Path, filename: str, data: dict) -> Path:
    fpath = rules_dir / filename
    with open(fpath, "w") as f:
        yaml.dump(data, f)
    return fpath


class TestRulePackLoader:
    def test_discover_files_empty_directory(
        self, loader: RulePackLoader, tmp_path: Path
    ) -> None:
        files = loader.discover_files()
        assert files == []

    def test_discover_files_missing_directory(self) -> None:
        loader = RulePackLoader("/nonexistent/path")
        files = loader.discover_files()
        assert files == []

    def test_discover_files_sorts_alphabetically(
        self, loader: RulePackLoader, tmp_path: Path
    ) -> None:
        rules_dir = Path(loader._rules_dir)
        _write_rule_pack(rules_dir, "z.yml", {"id": "z-pack"})
        _write_rule_pack(rules_dir, "a.yml", {"id": "a-pack"})
        _write_rule_pack(rules_dir, "m.yml", {"id": "m-pack"})
        files = loader.discover_files()
        assert len(files) == 3
        assert files[0].name == "a.yml"
        assert files[1].name == "m.yml"
        assert files[2].name == "z.yml"

    def test_load_file_valid(self, loader: RulePackLoader, tmp_path: Path) -> None:
        rules_dir = Path(loader._rules_dir)
        _write_rule_pack(
            rules_dir,
            "test.yml",
            {
                "id": "test-pack",
                "description": "Test pack",
                "rules": [
                    {
                        "id": "r1",
                        "type": "exclusion",
                        "config": {"function_types": ["EQ"]},
                    },
                ],
            },
        )
        files = loader.discover_files()
        assert len(files) == 1
        pack, result = loader.load_file(files[0])
        assert pack is not None
        assert pack.id == "test-pack"
        assert len(pack.rules) == 1
        assert pack.rules[0].id == "r1"
        assert result.status == "loaded"

    def test_load_file_invalid_yaml(
        self, loader: RulePackLoader, tmp_path: Path
    ) -> None:
        rules_dir = Path(loader._rules_dir)
        fpath = rules_dir / "bad.yml"
        fpath.write_text("{invalid: yaml: unclosed")
        pack, result = loader.load_file(fpath)
        assert pack is None
        assert result.status == "error"
        assert "Invalid YAML" in result.error

    def test_load_file_missing_id(self, loader: RulePackLoader, tmp_path: Path) -> None:
        rules_dir = Path(loader._rules_dir)
        _write_rule_pack(rules_dir, "noid.yml", {"description": "no id here"})
        files = loader.discover_files()
        pack, result = loader.load_file(files[0])
        assert pack is None
        assert result.status == "error"
        assert "missing required 'id'" in result.error

    def test_load_all_mixed_valid_and_invalid(
        self, loader: RulePackLoader, tmp_path: Path
    ) -> None:
        rules_dir = Path(loader._rules_dir)
        _write_rule_pack(rules_dir, "good.yml", {"id": "good-pack", "rules": []})
        _write_rule_pack(rules_dir, "bad.yml", {"description": "no id"})
        _write_rule_pack(rules_dir, "also-good.yml", {"id": "also-good", "rules": []})
        results = loader.load_all()
        assert len(results) == 3
        valid = [r for r in results if r[0] is not None]
        invalid = [r for r in results if r[0] is None]
        assert len(valid) == 2
        assert len(invalid) == 1
