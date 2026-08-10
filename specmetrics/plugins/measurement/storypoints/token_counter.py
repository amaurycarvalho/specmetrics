"""Token counting helpers for Story Points measurement."""

from __future__ import annotations

from specmetrics.kernel.token_utils import count_tokens


def count_tokens_for_element(name: str, description: str) -> int:
    """Return the token count for the given element name and description."""
    text = (name or "") + " " + (description or "")
    return count_tokens(text.strip())
