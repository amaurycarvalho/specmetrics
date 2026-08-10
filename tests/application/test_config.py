from __future__ import annotations

from pathlib import Path

from specmetrics.application.config import AppConfig


def _write_config(project_path: Path, content: str) -> Path:
    cfg_dir = project_path / ".specmetrics"
    cfg_dir.mkdir(parents=True)
    cfg_file = cfg_dir / "config.yml"
    cfg_file.write_text(content)
    return cfg_file


class TestAppConfigLoad:
    def test_missing_config_returns_defaults(self, tmp_path: Path) -> None:
        config = AppConfig.load(tmp_path / "empty")
        assert config.default_output_format == "text"
        assert config.verbose is False
        assert config.verify_compatibility is True

    def test_loads_config_from_specmetrics_dir(self, tmp_path: Path) -> None:
        project_path = tmp_path / "project"
        _write_config(
            project_path,
            "pipeline:\n  default_output_format: json\n  verbose: true\n"
            "plugins:\n  verify_compatibility: false\n",
        )
        config = AppConfig.load(project_path)
        assert config.default_output_format == "json"
        assert config.verbose is True
        assert config.verify_compatibility is False

    def test_empty_yaml_returns_defaults(self, tmp_path: Path) -> None:
        project_path = tmp_path / "project"
        _write_config(project_path, "")
        config = AppConfig.load(project_path)
        assert config.default_output_format == "text"

    def test_init_with_raw_mapping(self) -> None:
        config = AppConfig({"pipeline": {"default_output_format": "xml"}})
        assert config.default_output_format == "xml"
