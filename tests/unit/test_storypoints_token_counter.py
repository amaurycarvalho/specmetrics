from __future__ import annotations

from specmetrics.plugins.measurement.storypoints.token_counter import (
    count_tokens_for_element,
)


class TestCountTokensForElement:
    def test_empty_name_and_description(self):
        result = count_tokens_for_element("", "")
        assert result == 0

    def test_empty_name_with_description(self):
        result = count_tokens_for_element("", "hello world")
        assert result > 0

    def test_name_only(self):
        result = count_tokens_for_element("Process Order", "")
        assert result > 0

    def test_name_and_description(self):
        result = count_tokens_for_element(
            "Process Order",
            "System shall validate payment and process the order",
        )
        assert result > 0

    def test_long_description(self):
        long_text = "word " * 200
        result = count_tokens_for_element("Test", long_text)
        assert result > 0

    def test_short_text(self):
        result = count_tokens_for_element("a", "b")
        assert result > 0

    def test_deterministic(self):
        r1 = count_tokens_for_element("Process Order", "description text here")
        r2 = count_tokens_for_element("Process Order", "description text here")
        assert r1 == r2

    def test_different_inputs_different_outputs(self):
        r1 = count_tokens_for_element("Short", "tiny")
        r2 = count_tokens_for_element("Longer Name", "much longer description text here")
        assert r1 != r2
