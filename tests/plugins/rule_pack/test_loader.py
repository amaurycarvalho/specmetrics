from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from structlog.testing import capture_logs

from specmetrics.kernel.cfm.models import RuleConfig
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

    def test_default_rules_dir(self) -> None:
        loader = RulePackLoader()
        assert str(loader._rules_dir) == ".specmetrics/rules"

    def test_load_file_numeric_id_rejected(self, tmp_path: Path) -> None:
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        loader = RulePackLoader(str(rules_dir))
        fpath = _write_rule_pack(rules_dir, "numid.yml", {"id": 123})
        pack, result = loader.load_file(fpath)
        assert pack is None
        assert result.status == "error"
        assert "missing required 'id'" in result.error

    def test_load_file_root_not_mapping(
        self, loader: RulePackLoader, tmp_path: Path
    ) -> None:
        rules_dir = Path(loader._rules_dir)
        fpath = rules_dir / "listroot.yml"
        fpath.write_text("- just\n- a\n- list\n")
        pack, result = loader.load_file(fpath)
        assert pack is None
        assert result.status == "error"
        assert "must contain a mapping at root" in result.error

    def test_load_file_rule_defaults(self, loader: RulePackLoader, tmp_path: Path) -> None:
        rules_dir = Path(loader._rules_dir)
        _write_rule_pack(
            rules_dir,
            "meta.yml",
            {
                "id": "meta-pack",
                "rules": [
                    {"type": "exclusion", "config": {"function_types": ["EQ"]}},
                ],
            },
        )
        files = loader.discover_files()
        pack, _result = loader.load_file(files[0])
        assert pack is not None
        assert pack.description == ""
        assert pack.methodology == "FPA"
        assert pack.glossary_overrides == {}
        assert len(pack.rules) == 1
        assert pack.rules[0].id == ""
        assert pack.rules[0].description == ""
        assert pack.rules[0].config == RuleConfig(function_types=["EQ"])

    def test_load_file_explicit_metadata(
        self, loader: RulePackLoader, tmp_path: Path
    ) -> None:
        rules_dir = Path(loader._rules_dir)
        _write_rule_pack(
            rules_dir,
            "full.yml",
            {
                "id": "full-pack",
                "description": "A full pack",
                "methodology": "SNAP",
                "glossary_overrides": {"foo": "bar"},
                "rules": [],
            },
        )
        files = loader.discover_files()
        pack, result = loader.load_file(files[0])
        assert pack is not None
        assert pack.description == "A full pack"
        assert pack.methodology == "SNAP"
        assert pack.glossary_overrides == {"foo": "bar"}
        assert result.rules_count == 0
        assert result.rule_pack_id == "full-pack"

    def test_load_file_rules_is_string(self, loader: RulePackLoader, tmp_path: Path) -> None:
        rules_dir = Path(loader._rules_dir)
        _write_rule_pack(
            rules_dir, "stringrules.yml", {"id": "p", "rules": "not a list"}
        )
        files = loader.discover_files()
        pack, result = loader.load_file(files[0])
        assert pack is not None
        assert pack.rules == []
        assert result.rules_count == 0
        assert result.status == "loaded"

    def test_load_file_rule_without_config(
        self, loader: RulePackLoader, tmp_path: Path
    ) -> None:
        rules_dir = Path(loader._rules_dir)
        _write_rule_pack(
            rules_dir,
            "noconfig.yml",
            {"id": "p", "rules": [{"id": "r1", "type": "exclusion"}]},
        )
        files = loader.discover_files()
        pack, _result = loader.load_file(files[0])
        assert pack is not None
        assert pack.rules[0].config == RuleConfig()

    def test_load_file_preserves_rule_description(
        self, loader: RulePackLoader, tmp_path: Path
    ) -> None:
        rules_dir = Path(loader._rules_dir)
        _write_rule_pack(
            rules_dir,
            "desc.yml",
            {
                "id": "p",
                "rules": [
                    {
                        "id": "r1",
                        "type": "exclusion",
                        "description": "Exclude inquiries",
                        "config": {"function_types": ["EQ"]},
                    },
                ],
            },
        )
        files = loader.discover_files()
        pack, result = loader.load_file(files[0])
        assert result.file_path == str(files[0])
        assert pack is not None
        assert pack.rules[0].description == "Exclude inquiries"
        assert pack.rules[0].id == "r1"

    def test_load_file_no_config_rule_result(
        self, loader: RulePackLoader, tmp_path: Path
    ) -> None:
        rules_dir = Path(loader._rules_dir)
        _write_rule_pack(rules_dir, "m.yml", {"id": "p", "rules": []})
        files = loader.discover_files()
        _pack, result = loader.load_file(files[0])
        assert result.file_path == str(files[0])

    def test_load_file_non_dict_config_treated_as_empty(
        self, loader: RulePackLoader, tmp_path: Path
    ) -> None:
        rules_dir = Path(loader._rules_dir)
        _write_rule_pack(
            rules_dir,
            "strconfig.yml",
            {"id": "p", "rules": [{"id": "r1", "type": "exclusion", "config": "abc"}]},
        )
        files = loader.discover_files()
        pack, _result = loader.load_file(files[0])
        assert pack is not None
        assert pack.rules[0].config == RuleConfig()
        assert pack.rules[0].id == "r1"

    def test_discover_files_logs_dir_not_found(self) -> None:
        loader = RulePackLoader("/nonexistent/path")
        with capture_logs() as captured:
            assert loader.discover_files() == []
        assert any(
            e["event"] == "rule_pack_dir_not_found"
            and e["path"] == "/nonexistent/path"
            for e in captured
        )

    def test_discover_files_logs_found(self, loader: RulePackLoader, tmp_path: Path) -> None:
        rules_dir = Path(loader._rules_dir)
        _write_rule_pack(rules_dir, "a.yml", {"id": "a"})
        with capture_logs() as captured:
            files = loader.discover_files()
        assert len(files) == 1
        assert any(
            e["event"] == "rule_pack_files_discovered"
            and e["count"] == 1
            and e["path"] == str(rules_dir)
            for e in captured
        )

    def test_load_file_logs_parse_error(self, tmp_path: Path) -> None:
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        loader = RulePackLoader(str(rules_dir))
        fpath = rules_dir / "bad.yml"
        fpath.write_text("{invalid: yaml: unclosed")
        with capture_logs() as captured:
            pack, result = loader.load_file(fpath)
        assert pack is None
        assert result.status == "error"
        assert any(
            e["event"] == "rule_pack_parse_error"
            and e["file"] == str(fpath)
            and e["error"]
            and e["error"] != "None"
            for e in captured
        )
