from __future__ import annotations

from specmetrics.infrastructure.config.schema import CoreConfig
from specmetrics.infrastructure.config.validator import (
    ConfigValidationError,
    ConfigParseError,
    Validator,
)


class TestValidator:
    def test_valid_data_passes(self):
        validator = Validator(CoreConfig)
        result = validator.validate({"pipeline": {"stage_timeout": 30}})
        assert result.pipeline.stage_timeout == 30

    def test_invalid_data_raises_error(self):
        validator = Validator(CoreConfig)
        import pytest

        with pytest.raises(ConfigValidationError):
            validator.validate({"pipeline": {"stage_timeout": "not-a-number"}})

    def test_unrecognized_key_warning(self):
        validator = Validator(CoreConfig)
        warnings = validator.check_unrecognized_keys({"unknown_key": 1})
        assert len(warnings) == 1
        assert "unknown_key" in warnings[0].message

    def test_known_prefix_suppresses_warning(self):
        validator = Validator(CoreConfig)
        warnings = validator.check_unrecognized_keys(
            {"plugins.my_plugin.x": 1}, known_prefixes=["plugins"]
        )
        assert len(warnings) == 0


class TestConfigValidationError:
    def test_error_attributes(self):
        err = ConfigValidationError(
            message="test error",
            field="pipeline.timeout",
            value="abc",
            expected_type="integer",
        )
        assert err.field == "pipeline.timeout"
        assert err.value == "abc"
        assert err.expected_type == "integer"
        assert "test error" in str(err)


class TestConfigParseError:
    def test_error_attributes(self):
        err = ConfigParseError(
            message="parse error",
            file_path="/path/to/config.yml",
            line_number=10,
        )
        assert err.file_path == "/path/to/config.yml"
        assert err.line_number == 10
