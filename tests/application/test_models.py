from __future__ import annotations

from specmetrics.application.models import (
    is_valid_entity_id,
    make_entity_id,
    resolve_entity_id,
)


class TestIsValidEntityId:
    def test_valid_compound_uri(self) -> None:
        assert is_valid_entity_id("cfm:data_group:user-profile") is True

    def test_valid_csm_id(self) -> None:
        assert is_valid_entity_id("csm:specification_activity:review") is True

    def test_invalid_string(self) -> None:
        assert is_valid_entity_id("plain-string") is False

    def test_invalid_missing_prefix(self) -> None:
        assert is_valid_entity_id("data_group:user-profile") is False


class TestResolveEntityId:
    def test_valid_raw_id_returned_as_is(self) -> None:
        assert (
            resolve_entity_id("cfm:data_group:profile", "data_group", "Profile")
            == "cfm:data_group:profile"
        )

    def test_invalid_raw_id_builds_from_category_and_name(self) -> None:
        result = resolve_entity_id("plain-string", "data_group", "User Profile")
        assert result == "cfm:data_group:user-profile"

    def test_empty_raw_id_builds_from_category_and_name(self) -> None:
        assert resolve_entity_id("", "actor", "System User") == "cfm:actor:system-user"

    def test_csm_model_source(self) -> None:
        assert (
            resolve_entity_id("", "specification_activity", "Clarify x", "csm")
            == "csm:specification_activity:clarify-x"
        )

    def test_built_id_is_valid(self) -> None:
        result = resolve_entity_id("", "operation", "Register User")
        assert is_valid_entity_id(result)


class TestMakeEntityId:
    def test_basic_id(self) -> None:
        assert make_entity_id("data_group", "User Profile") == "cfm:data_group:user-profile"

    def test_normalizes_spaces_and_case(self) -> None:
        assert make_entity_id("actor", "System User") == "cfm:actor:system-user"

    def test_invalid_model_source_defaults_to_cfm(self) -> None:
        assert make_entity_id("actor", "User", "xx") == "cfm:actor:user"

    def test_csm_model_source(self) -> None:
        assert make_entity_id("operation", "Login", "csm") == "csm:operation:login"

    def test_collapses_repeated_dashes(self) -> None:
        assert make_entity_id("data_group", "A--B") == "cfm:data_group:a-b"
