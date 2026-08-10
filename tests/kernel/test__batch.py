from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from structlog.testing import capture_logs

from specmetrics.kernel._batch import BatchMixin
from specmetrics.kernel._models import BatchRequest, DocumentPayload


def _stub(batch_max_chars: int = 100000) -> BatchMixin:
    stub = BatchMixin.__new__(BatchMixin)
    stub.config = SimpleNamespace(batch_max_chars=batch_max_chars, model="gpt-4o-mini")
    return stub


def _batch() -> BatchRequest:
    docs = [DocumentPayload("doc1", "content1", "spec")]
    return BatchRequest(system_prompt="sys", documents=docs)


def test_complete_batch_default_json_mode_is_true() -> None:
    """Kills BatchMixin::complete_batch__mutmut_1 (``json_mode: bool = True`` -> ``False``)."""
    stub = _stub()
    stub.complete = MagicMock(
        return_value=json.dumps({"doc1": {"elements": [{"a": 1}]}})
    )
    stub.complete_batch(_batch())
    assert stub.complete.call_args.kwargs["json_mode"] is True


def test_complete_batch_success_path_passes_expected_arguments() -> None:
    """Kills complete_batch__mutmut_5 (provider=None), mutmut_7 (user_message=None), mutmut_9 (json_instruction provider), mutmut_10 (system_prompt=None), mutmut_13/14/15/18 (complete call args)."""
    stub = _stub()
    stub.complete = MagicMock(
        return_value=json.dumps({"doc1": {"elements": [{"a": 1}]}})
    )
    batch = _batch()
    result = stub.complete_batch(batch)
    assert result == {"doc1": [{"a": 1}]}
    sub_batch = batch.split(stub.config.batch_max_chars)[0]
    kwargs = stub.complete.call_args.kwargs
    assert kwargs["system_prompt"] == "sys"
    assert kwargs["user_message"] == sub_batch.assemble_prompt()
    assert kwargs["json_mode"] is True


def test_complete_batch_retries_individual_documents_on_batch_failure() -> None:
    """Kills complete_batch__mutmut_30/31/32 (doc_count log), mutmut_35/38/41 (single_prompt), mutmut_36 (response_text=None), mutmut_37/39/40/42 (single complete args), mutmut_43/45/47/48 (single_batch construction), mutmut_50..56/58 (parsing and result assignment)."""
    stub = _stub()
    calls = {"n": 0}
    call_kwargs: list = []

    def fake_complete(**kwargs):
        calls["n"] += 1
        call_kwargs.append(kwargs)
        if calls["n"] == 1:
            raise ValueError("batch response failed")
        return json.dumps({"doc1": {"elements": [{"ok": 1}]}})

    stub.complete = fake_complete
    with capture_logs() as logs:
        result = stub.complete_batch(_batch())
    assert result == {"doc1": [{"ok": 1}]}
    single_kwargs = call_kwargs[1]
    assert single_kwargs["system_prompt"] == "sys"
    assert single_kwargs["user_message"] == 'Document "doc1": content1'
    assert single_kwargs["json_mode"] is True
    entry = next(l for l in logs if l["event"] == "batch_failed_retrying_individual")
    assert entry["doc_count"] == 1


def test_complete_batch_records_individual_failures() -> None:
    """Kills complete_batch__mutmut_61/62/63 (individual_doc_failed log) and mutmut_66 (``= []`` -> ``= None``)."""
    stub = _stub()
    stub.complete = MagicMock(side_effect=ValueError("always fails"))
    with capture_logs() as logs:
        result = stub.complete_batch(_batch())
    assert result == {"doc1": []}
    entry = next(l for l in logs if l["event"] == "individual_doc_failed")
    assert entry["doc_id"] == "doc1"
