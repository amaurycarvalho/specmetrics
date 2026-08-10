"""Token counting utilities with a tiktoken-backed primary implementation."""

from __future__ import annotations

try:
    import tiktoken

    _enc = tiktoken.get_encoding("cl100k_base")

    def count_tokens(text: str) -> int:
        """Return the number of tokens in the given text."""
        return len(_enc.encode(text))

except ImportError:
    import logging

    _LOGGER = logging.getLogger(__name__)
    _LOGGER.warning(
        "tiktoken not installed — using character-count fallback (4 chars ≈ 1 token)"
    )

    def count_tokens(text: str) -> int:
        """Return an approximate token count based on character length."""
        return max(1, len(text) // 4)
