from __future__ import annotations

from specmetrics.kernel.cfm.model import (
    BuildMetadata,
    CanonicalFunctionalModel,
    EvidenceRef,
    FunctionalProcess,
)
from specmetrics.plugins.measurement.bcp._measure import (
    make_failed_item,
    make_success_item,
    measure_all,
)
from specmetrics.plugins.measurement.bcp.models import SDKResult


def _make_cfm() -> CanonicalFunctionalModel:
    ev = EvidenceRef(graph_node_id="gn-1", document_id="doc-1", text="ev")
    fps = {}
    for i in range(2):
        fid = f"fp-{i}"
        fps[fid] = FunctionalProcess(id=fid, name=f"Process {i}", evidence=ev)
    return CanonicalFunctionalModel(
        run_id="cfm-test",
        functional_processes=fps,
        metadata=BuildMetadata(run_id="cfm-test"),
    )


class _FakeAdapter:
    def __init__(self, results: list[SDKResult]) -> None:
        self._results = results
        self.calls: list[str] = []

    def calculate(self, story: str) -> SDKResult:
        self.calls.append(story)
        return self._results.pop(0)


class TestMakeFailedItem:
    def _fp(self):
        return FunctionalProcess(
            id="fp-x",
            name="Login",
            evidence=EvidenceRef(
                graph_node_id="gn", document_id="doc-9", text="evidence text"
            ),
        )

    def test_without_evidence(self):
        item = make_failed_item(
            "fp-x",
            self._fp(),
            "# story",
            SDKResult(total_bcp=0.0, raw_response={"k": "v"}, errors=["e1"]),
            include_evidence=False,
        )
        assert item.status == "failed"
        assert item.bcp_score == 0.0
        assert item.element_name == "Login"
        assert item.sdk_response == {"k": "v"}
        assert item.evidence_refs == []

    def test_with_evidence(self):
        item = make_failed_item(
            "fp-x",
            self._fp(),
            "# story",
            SDKResult(total_bcp=0.0, errors=["e1"]),
            include_evidence=True,
        )
        assert len(item.evidence_refs) == 1
        assert item.evidence_refs[0].document_id == "doc-9"
        assert item.evidence_refs[0].text == "evidence text"

    def test_evidence_fallback_to_empty(self):
        class BareFP:
            name = "Login"
            evidence = None

        item = make_failed_item(
            "fp-x",
            BareFP(),
            "# story",
            SDKResult(total_bcp=0.0, errors=["e1"]),
            include_evidence=True,
        )
        assert item.evidence_refs[0].document_id == ""
        assert item.evidence_refs[0].text == ""


class TestMakeSuccessItem:
    def _fp(self):
        return FunctionalProcess(
            id="fp-x",
            name="Login",
            evidence=EvidenceRef(
                graph_node_id="gn", document_id="doc-9", text="evidence text"
            ),
        )

    def test_without_evidence(self):
        item = make_success_item(
            "fp-x",
            self._fp(),
            "# story",
            SDKResult(total_bcp=12.5, breakdown={"bl": 8.0}, duration_ms=4.0),
            include_evidence=False,
        )
        assert item.status == "success"
        assert item.bcp_score == 12.5
        assert item.component_breakdown == {"bl": 8.0}
        assert item.evidence_refs == []

    def test_with_evidence(self):
        item = make_success_item(
            "fp-x",
            self._fp(),
            "# story",
            SDKResult(total_bcp=12.5),
            include_evidence=True,
        )
        assert item.status == "success"
        assert len(item.evidence_refs) == 1
        assert item.evidence_refs[0].element_id == "fp-x"
        assert item.evidence_refs[0].document_id == "doc-9"
        assert item.evidence_refs[0].text == "evidence text"

    def test_evidence_fallback_to_empty(self):
        class BareFP:
            name = "Login"
            evidence = None

        item = make_success_item(
            "fp-x",
            BareFP(),
            "# story",
            SDKResult(total_bcp=12.5),
            include_evidence=True,
        )
        assert item.evidence_refs[0].document_id == ""
        assert item.evidence_refs[0].text == ""


class TestMeasureAll:
    def test_success_flow_tracks_callbacks(self):
        adapter = _FakeAdapter(
            [
                SDKResult(total_bcp=10.0, breakdown={"bl": 10.0}, duration_ms=3.0),
                SDKResult(total_bcp=5.0, breakdown={"data": 5.0}, duration_ms=2.0),
            ]
        )
        requests: list[str] = []
        durations: list[float] = []

        items, succeeded, failed, sdk_calls, sdk_errors = measure_all(
            _make_cfm(),
            adapter,
            record_request=lambda: requests.append("r"),
            record_success=lambda d: durations.append(d),
            include_evidence=False,
        )

        assert succeeded == 2
        assert failed == 0
        assert sdk_calls == 2
        assert sdk_errors == 0
        assert len(requests) == 2
        assert durations == [3.0, 2.0]
        assert [i.status for i in items] == ["success", "success"]

    def test_error_flow_tracks_callbacks(self):
        adapter = _FakeAdapter(
            [
                SDKResult(total_bcp=0.0, errors=["e1", "e2"]),
                SDKResult(total_bcp=0.0, errors=["e3"]),
            ]
        )
        error_counts: list[int] = []

        items, succeeded, failed, sdk_calls, sdk_errors = measure_all(
            _make_cfm(),
            adapter,
            record_error=lambda n: error_counts.append(n),
            include_evidence=True,
        )

        assert succeeded == 0
        assert failed == 2
        assert sdk_calls == 2
        assert sdk_errors == 3
        assert error_counts == [2, 1]
        assert items[0].status == "failed"
        assert items[1].status == "failed"
        assert len(items[0].evidence_refs) == 1

    def test_mixed_flow_without_callbacks(self):
        adapter = _FakeAdapter(
            [
                SDKResult(total_bcp=8.0),
                SDKResult(total_bcp=0.0, errors=["x"]),
            ]
        )
        items, succeeded, failed, sdk_calls, sdk_errors = measure_all(
            _make_cfm(),
            adapter,
            include_evidence=False,
        )
        assert succeeded == 1
        assert failed == 1
        assert sdk_calls == 2
        assert sdk_errors == 1
        assert items[0].status == "success"
        assert items[1].status == "failed"

    def test_empty_cfm_returns_no_items(self):
        cfm = CanonicalFunctionalModel(
            run_id="empty",
            metadata=BuildMetadata(run_id="empty"),
        )
        adapter = _FakeAdapter([])
        items, succeeded, failed, sdk_calls, sdk_errors = measure_all(
            cfm, adapter, include_evidence=False
        )
        assert items == []
        assert succeeded == 0
        assert failed == 0
        assert sdk_calls == 0
        assert sdk_errors == 0

    def test_passes_generated_story_to_adapter(self):
        adapter = _FakeAdapter([SDKResult(total_bcp=1.0), SDKResult(total_bcp=2.0)])
        measure_all(_make_cfm(), adapter, include_evidence=False)
        assert len(adapter.calls) == 2
        assert all(isinstance(s, str) and s for s in adapter.calls)

    def test_success_with_evidence_populates_refs(self):
        adapter = _FakeAdapter(
            [
                SDKResult(total_bcp=1.0),
                SDKResult(total_bcp=2.0),
            ]
        )
        items, succeeded, _failed, _sdk_calls, _sdk_errors = measure_all(
            _make_cfm(), adapter, include_evidence=True
        )
        assert succeeded == 2
        assert all(len(item.evidence_refs) == 1 for item in items)