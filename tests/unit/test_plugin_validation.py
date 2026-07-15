from unittest.mock import patch

from specmetrics.kernel import (
    EventType,
    PluginMetadata,
    PluginType,
    PluginValidator,
)
from specmetrics.kernel.plugin_validation import ValidationResult


def _make_metadata(**overrides) -> PluginMetadata:
    fields = {
        "id": "test-plugin",
        "api_version": "1.0.0",
        "plugin_type": PluginType.ADAPTER,
        "handled_event_types": (),
        "handler_factory": None,
        "name": None,
        "description": None,
        "author": None,
        "version": None,
    }
    fields.update(overrides)
    return PluginMetadata(**fields)


class TestPluginValidator:
    def test_rejects_incompatible_major_api_version(self) -> None:
        with patch("specmetrics.kernel.plugin_validation.version", return_value="1.0.0"):
            validator = PluginValidator()
            meta = _make_metadata(api_version="2.0.0")
            result = validator.validate(meta)

        assert not result.is_valid
        assert any("major version mismatch" in e for e in result.errors)

    def test_accepts_compatible_api_version(self) -> None:
        with patch("specmetrics.kernel.plugin_validation.version", return_value="1.0.0"):
            validator = PluginValidator()
            meta = _make_metadata(api_version="1.5.2")
            result = validator.validate(meta)

        assert result.is_valid

    def test_accepts_exact_api_version_match(self) -> None:
        with patch("specmetrics.kernel.plugin_validation.version", return_value="1.0.0"):
            validator = PluginValidator()
            meta = _make_metadata(api_version="1.0.0")
            result = validator.validate(meta)

        assert result.is_valid

    def test_rejects_unparseable_version_string(self) -> None:
        with patch("specmetrics.kernel.plugin_validation.version", return_value="1.0.0"):
            validator = PluginValidator()
            meta = _make_metadata(api_version="not-a-version")
            result = validator.validate(meta)

        assert not result.is_valid
        assert any("Unparseable" in e for e in result.errors)

    def test_rejects_missing_required_fields(self) -> None:
        with patch("specmetrics.kernel.plugin_validation.version", return_value="1.0.0"):
            validator = PluginValidator()
            meta = _make_metadata(id="", api_version="")
            result = validator.validate(meta)

        assert not result.is_valid
        assert any("id" in e for e in result.errors)
        assert any("api_version" in e for e in result.errors)

    def test_rejects_unspecified_plugin_type(self) -> None:
        with patch("specmetrics.kernel.plugin_validation.version", return_value="1.0.0"):
            validator = PluginValidator()
            meta = _make_metadata(plugin_type=PluginType.UNSPECIFIED)
            result = validator.validate(meta)

        assert not result.is_valid
        assert any("Plugin type must be specified" in e for e in result.errors)

    def test_rejects_missing_handler_factory_when_handled_events_declared(self) -> None:
        with patch("specmetrics.kernel.plugin_validation.version", return_value="1.0.0"):
            validator = PluginValidator()
            meta = _make_metadata(
                handled_event_types=(EventType.REPOSITORY_LOADED,),
                handler_factory=None,
            )
            result = validator.validate(meta)

        assert not result.is_valid
        assert any("handler_factory" in e for e in result.errors)

    def test_accepts_handler_factory_when_handled_events_declared(self) -> None:
        with patch("specmetrics.kernel.plugin_validation.version", return_value="1.0.0"):
            validator = PluginValidator()
            meta = _make_metadata(
                handled_event_types=(EventType.REPOSITORY_LOADED,),
                handler_factory=lambda: None,
            )
            result = validator.validate(meta)

        assert result.is_valid

    def test_validation_result_dataclass(self) -> None:
        result = ValidationResult(is_valid=True)
        assert result.is_valid
        assert result.errors == []

        result2 = ValidationResult(is_valid=False, errors=["err1"])
        assert not result2.is_valid
        assert result2.errors == ["err1"]
