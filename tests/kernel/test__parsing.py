from __future__ import annotations

import json

import pytest

from specmetrics.kernel._models import BatchRequest, DocumentPayload
from specmetrics.kernel._parsing import parse_batch_response


def _batch(*doc_ids: str) -> BatchRequest:
    return BatchRequest(
        system_prompt="sys",
        documents=[
            DocumentPayload(document_id=doc_id, content="text", document_type="spec")
            for doc_id in doc_ids
        ],
    )


class TestParseBatchResponse:
    def test_dict_elements_extracted(self) -> None:
        result = parse_batch_response(
            json.dumps({"doc-1": {"elements": [{"type": "fact"}]}}),
            _batch("doc-1"),
        )
        assert result["doc-1"] == [{"type": "fact"}]

    def test_list_format_response(self) -> None:
        result = parse_batch_response(
            json.dumps({"doc-1": [{"type": "fact"}]}),
            _batch("doc-1"),
        )
        assert result["doc-1"] == [{"type": "fact"}]

    def test_non_object_response_raises_type_error(self) -> None:
        with pytest.raises(TypeError, match="Batch response is not a JSON object"):
            parse_batch_response("[]", _batch("doc-1"))

    def test_missing_document_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Batch response missing document IDs"):
            parse_batch_response(
                json.dumps({"doc-1": {"elements": []}}),
                _batch("doc-1", "doc-2"),
            )

    def test_missing_document_message_lists_ids(self) -> None:
        with pytest.raises(ValueError) as excinfo:
            parse_batch_response(
                json.dumps({"doc-1": {"elements": []}}),
                _batch("doc-2", "doc-3"),
            )
        assert str(excinfo.value) == "Batch response missing document IDs: doc-2, doc-3"

    def test_dict_without_elements_returns_empty_list(self) -> None:
        result = parse_batch_response(
            json.dumps({"doc-1": {"other": 1}}),
            _batch("doc-1"),
        )
        assert result["doc-1"] == []

    def test_scalar_doc_data_returns_empty_list(self) -> None:
        result = parse_batch_response(
            json.dumps({"doc-1": 42}),
            _batch("doc-1"),
        )
        assert result["doc-1"] == []
