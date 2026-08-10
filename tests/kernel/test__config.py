from __future__ import annotations

from pathlib import Path

from specmetrics.kernel import _config
from specmetrics.kernel._config import LLMGatewayConfig, load_llm_config_rpm


def _config_dir(tmp_path: Path) -> Path:
    d = tmp_path / "specmetrics"
    d.mkdir()
    return d


def test_load_llm_config_rpm_reads_config_yml(tmp_path, monkeypatch) -> None:
    """Kills load_llm_config_rpm__mutmut_1/2 (config.yml literal), mutmut_9/11/12 (YAML typ), mutmut_13/14/16/17 (yaml.load), mutmut_18 (rpm=None), mutmut_19/39/40 (rpm_limit key), mutmut_22/37/38 (llm key), mutmut_26/35/36 (extraction_stage key), mutmut_30/33/34 (plugins key), mutmut_41 (``is not None`` -> ``is None``), mutmut_42 (``int(rpm)`` -> ``int(None)``)."""
    d = _config_dir(tmp_path)
    (d / "config.yml").write_text(
        "plugins:\n  extraction_stage:\n    llm:\n      rpm_limit: 42\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(_config, "_CONFIG_SEARCH_PATHS", [d])
    assert load_llm_config_rpm() == 42


def test_load_llm_config_rpm_reads_config_yaml(tmp_path, monkeypatch) -> None:
    """Kills load_llm_config_rpm__mutmut_3/4 (config.yaml literal)."""
    d = _config_dir(tmp_path)
    (d / "config.yaml").write_text(
        "plugins:\n  extraction_stage:\n    llm:\n      rpm_limit: 7\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(_config, "_CONFIG_SEARCH_PATHS", [d])
    assert load_llm_config_rpm() == 7


def test_load_llm_config_rpm_reads_config_json(tmp_path, monkeypatch) -> None:
    """Kills load_llm_config_rpm__mutmut_5/6 (config.json literal)."""
    d = _config_dir(tmp_path)
    (d / "config.json").write_text(
        '{"plugins": {"extraction_stage": {"llm": {"rpm_limit": 99}}}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(_config, "_CONFIG_SEARCH_PATHS", [d])
    assert load_llm_config_rpm() == 99


def test_load_llm_config_rpm_returns_none_without_config(tmp_path, monkeypatch) -> None:
    """Kills load_llm_config_rpm__mutmut_1..6 (filename iteration defaults)."""
    d = _config_dir(tmp_path)
    monkeypatch.setattr(_config, "_CONFIG_SEARCH_PATHS", [d])
    assert load_llm_config_rpm() is None


def test_gateway_config_defaults(monkeypatch) -> None:
    """Kills LLMGatewayConfig::__init____mutmut_1/2 (provider literal) and mutmut_3/4 (model literal)."""
    monkeypatch.delenv("SPECMETRICS_LLM_RPM_LIMIT", raising=False)
    config = LLMGatewayConfig()
    assert config.provider == "openai"
    assert config.model == "gpt-4o-mini"


def test_gateway_config_max_tokens(monkeypatch) -> None:
    """Kills LLMGatewayConfig::__init____mutmut_9 (``self.max_tokens = None``)."""
    monkeypatch.delenv("SPECMETRICS_LLM_RPM_LIMIT", raising=False)
    config = LLMGatewayConfig(max_tokens=100)
    assert config.max_tokens == 100


def test_gateway_config_invalid_env_uses_default_rpm(monkeypatch) -> None:
    """Kills LLMGatewayConfig::__init____mutmut_21 (``self.rpm_limit = None``)."""
    monkeypatch.setenv("SPECMETRICS_LLM_RPM_LIMIT", "not-a-number")
    config = LLMGatewayConfig(rpm_limit=None)
    assert config.rpm_limit == 15


def test_gateway_config_reads_rpm_from_config_file(tmp_path, monkeypatch) -> None:
    """Kills LLMGatewayConfig::__init____mutmut_22 (``cfg_rpm = None``)."""
    d = _config_dir(tmp_path)
    (d / "config.yml").write_text(
        "plugins:\n  extraction_stage:\n    llm:\n      rpm_limit: 42\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(_config, "_CONFIG_SEARCH_PATHS", [d])
    monkeypatch.delenv("SPECMETRICS_LLM_RPM_LIMIT", raising=False)
    config = LLMGatewayConfig(rpm_limit=None)
    assert config.rpm_limit == 42
