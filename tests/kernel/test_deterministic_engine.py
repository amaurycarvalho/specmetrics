from __future__ import annotations

import inspect

from structlog.testing import capture_logs

from specmetrics.kernel.deterministic_engine import DeterministicSemanticEngine


class _FakeDoc:
    id = "doc-1"


class TestDeterministicEngineInit:
    def test_default_max_heading_depth_is_six(self) -> None:
        sig = inspect.signature(DeterministicSemanticEngine.__init__)
        assert sig.parameters["max_heading_depth"].default == 6

    def test_default_confidence_is_070(self) -> None:
        sig = inspect.signature(DeterministicSemanticEngine.__init__)
        assert sig.parameters["default_confidence"].default == 0.70

    def test_max_heading_depth_stored(self) -> None:
        engine = DeterministicSemanticEngine(max_heading_depth=4)
        assert engine._max_heading_depth == 4
        assert DeterministicSemanticEngine()._max_heading_depth == 6

    def test_default_rule_pack_stored(self) -> None:
        engine = DeterministicSemanticEngine(default_rule_pack="default-pack")
        assert engine._default_rule_pack == "default-pack"

    def test_default_confidence_stored(self) -> None:
        engine = DeterministicSemanticEngine(default_confidence=0.9)
        assert engine._default_confidence == 0.9
        assert DeterministicSemanticEngine()._default_confidence == 0.70

    def test_pattern_library_starts_none(self) -> None:
        assert DeterministicSemanticEngine()._pattern_library is None

    def test_extra_rule_packs_defaults_to_empty(self) -> None:
        assert DeterministicSemanticEngine()._extra_rule_packs == []


class TestLogLowSuccess:
    def _engine(self) -> DeterministicSemanticEngine:
        return DeterministicSemanticEngine()

    def test_logs_low_success_fields(self) -> None:
        with capture_logs() as captured:
            self._engine()._log_low_success(
                _FakeDoc(),
                success_rate=88.888,
                attempted=9,
                succeeded=8,
                failed=1,
                failed_ids={"r2", "r1"},
                duration=42,
            )
        assert len(captured) == 1
        event = captured[0]
        assert event["event"] == "low_extraction_success_rate"
        assert event["document_id"] == "doc-1"
        assert event["success_rate"] == round(88.888, 2)
        assert event["rules_attempted"] == 9
        assert event["rules_succeeded"] == 8
        assert event["rules_failed"] == 1
        assert event["failed_rule_ids"] == ["r1", "r2"]
        assert event["duration_ms"] == 42
