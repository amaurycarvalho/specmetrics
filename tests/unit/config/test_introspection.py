from __future__ import annotations

from pydantic import SecretStr

from specmetrics.infrastructure.config.introspection import (
    _is_sensitive_value,
    _mask_if_sensitive,
    build_dump,
)
from specmetrics.infrastructure.config.schema import (
    CoreConfig,
    ResolvedConfiguration,
)


class TestSensitiveValue:
    def test_secret_str_is_sensitive(self):
        assert _is_sensitive_value(SecretStr("secret")) is True

    def test_plain_string_not_sensitive(self):
        assert _is_sensitive_value("hello") is False

    def test_mask_secret_str(self):
        result = _mask_if_sensitive(SecretStr("secret"), True)
        assert result == "**********"

    def test_skip_non_sensitive(self):
        result = _mask_if_sensitive("hello", False)
        assert result == "hello"


class TestBuildDump:
    def test_empty_config(self):
        config = ResolvedConfiguration(values=CoreConfig())
        dump = build_dump(config)
        assert len(dump.entries) >= 0
