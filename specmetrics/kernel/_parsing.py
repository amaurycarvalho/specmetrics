"""Parsing helpers for LLM batch responses."""

from __future__ import annotations

import json
from typing import Any

from ._models import BatchRequest


def parse_batch_response(
    response_text: str, batch: BatchRequest
) -> dict[str, list[dict[str, Any]]]:
    """Parse batch response text into per-document element lists."""
    data = json.loads(response_text)
    if not isinstance(data, dict):
        raise TypeError("Batch response is not a JSON object")

    expected_ids = {doc.document_id for doc in batch.documents}
    returned_ids = set(data.keys())
    missing_ids = expected_ids - returned_ids
    if missing_ids:
        raise ValueError(
            f"Batch response missing document IDs: {', '.join(sorted(missing_ids))}"
        )

    results: dict[str, list[dict[str, Any]]] = {}
    for doc in batch.documents:
        doc_id = doc.document_id
        doc_data = data.get(doc_id, {})
        if isinstance(doc_data, dict):
            results[doc_id] = doc_data.get("elements", [])
        elif isinstance(doc_data, list):
            results[doc_id] = doc_data
        else:
            results[doc_id] = []
    return results