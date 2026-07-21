from __future__ import annotations

from specmetrics.kernel.token_utils import count_tokens


def count_tokens_for_element(name: str, description: str) -> int:
    text = (name or "") + " " + (description or "")
    return count_tokens(text.strip())
