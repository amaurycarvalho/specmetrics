from __future__ import annotations

from specmetrics.kernel.engine_patterns import PatternLibrary
from specmetrics.kernel.engine_rule import ExtractionRule
from specmetrics.kernel.engine_visitors import Observation


def _rule(
    rid: str,
    heading: str = "",
    keywords: list[str] | None = None,
    priority: int = 50,
) -> ExtractionRule:
    pattern: dict = {}
    if heading:
        pattern["heading"] = heading
    if keywords:
        pattern["keywords"] = keywords
        pattern["min_matches"] = len(keywords)
    return ExtractionRule(
        id=rid,
        name=rid,
        pattern=pattern,
        type="entity" if heading else "fact",
        confidence=0.9,
        priority=priority,
    )


def _obs(type_: str = "heading", content: str = "", section_type: str = "") -> Observation:
    return Observation(
        type=type_,
        content=content,
        context={"section_type": section_type},
        location=("doc-1", None),
    )


class TestPatternLibraryInitialization:
    def test_empty_pack_list(self) -> None:
        lib = PatternLibrary([])
        assert lib.rules == []

    def test_single_pack(self) -> None:
        lib = PatternLibrary([[_rule("r1", heading="Actors")]])
        assert len(lib.rules) == 1

    def test_multiple_packs_merged(self) -> None:
        lib = PatternLibrary([
            [_rule("r1", heading="Actors")],
            [_rule("r2", heading="Constraints")],
        ])
        assert len(lib.rules) == 2


class TestPatternLibraryConflictResolution:
    def test_higher_priority_overrides_lower(self) -> None:
        lib = PatternLibrary([
            [_rule("dup", heading="Actors", priority=50)],
            [_rule("dup", heading="Actors", priority=90)],
        ])
        assert lib.rules[0].priority == 90

    def test_same_priority_tie_broken_by_id(self) -> None:
        lib = PatternLibrary([
            [_rule("b-rule", heading="Test", priority=50)],
            [_rule("a-rule", heading="Test", priority=50)],
        ])
        ids = [r.id for r in lib.rules]
        assert ids == sorted(ids)


class TestPatternLibraryMatching:
    def test_heading_match(self) -> None:
        lib = PatternLibrary([[_rule("actors", heading="Actors")]])
        obs = [_obs(content="Actors", section_type="Actors")]
        elements = lib.match(obs)
        assert len(elements) == 1

    def test_no_match(self) -> None:
        lib = PatternLibrary([[_rule("actors", heading="Actors")]])
        obs = [_obs(content="Unknown", section_type="Unknown")]
        elements = lib.match(obs)
        assert len(elements) == 0

    def test_empty_observations(self) -> None:
        lib = PatternLibrary([[_rule("actors", heading="Actors")]])
        elements = lib.match([])
        assert len(elements) == 0
