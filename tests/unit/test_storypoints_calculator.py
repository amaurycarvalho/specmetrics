from __future__ import annotations

import uuid
import time

import pytest

from specmetrics.kernel.cfm.model import (
    Actor,
    BusinessRule,
    CanonicalFunctionalModel,
    DataGroup,
    EvidenceRef,
    FunctionalProcess,
    Operation,
    Relationship,
    BuildMetadata,
)
from specmetrics.plugins.measurement.storypoints.calculator import calculate
from specmetrics.plugins.measurement.storypoints.models import (
    StoryPointMeasurementResult,
)


def _uid() -> str:
    return str(uuid.uuid4())


def _make_evidence(text: str = "evidence") -> EvidenceRef:
    return EvidenceRef(
        graph_node_id="gn-001", document_id="doc-001", text=text
    )


def _make_cfm(
    fp_count: int = 2,
    actors_per_fp: int = 1,
    ops_per_fp: int = 1,
    br_per_fp: int = 0,
    rels_per_fp: int = 0,
) -> CanonicalFunctionalModel:
    actors: dict[str, Actor] = {}
    fps: dict[str, FunctionalProcess] = {}
    brs: dict[str, BusinessRule] = {}
    dgs: dict[str, DataGroup] = {}
    ops: dict[str, Operation] = {}
    rels: list[Relationship] = []

    for i in range(fp_count):
        ev = _make_evidence(text=f"Process {i} evidence")
        fp_id = _uid()
        fp_actors = []
        for j in range(actors_per_fp):
            aid = _uid()
            actors[aid] = Actor(id=aid, name=f"Actor {i}-{j}", evidence=ev)
            fp_actors.append(aid)

        fp_dgs = []
        for j in range(1):
            dgid = _uid()
            dgs[dgid] = DataGroup(id=dgid, name=f"DG {i}-{j}", evidence=ev)
            fp_dgs.append(dgid)

        fp_ops = []
        for j in range(ops_per_fp):
            oid = _uid()
            ops[oid] = Operation(
                id=oid,
                name=f"Op {i}-{j}",
                parent_process_id=fp_id,
                evidence=ev,
            )
            fp_ops.append(oid)

        for j in range(br_per_fp):
            brid = _uid()
            brs[brid] = BusinessRule(
                id=brid,
                name=f"BR {i}-{j}",
                related_process_ids=[fp_id],
                evidence=ev,
            )

        for j in range(rels_per_fp):
            rel_id = _uid()
            rels.append(
                Relationship(
                    id=rel_id,
                    source_id=fp_id,
                    target_id=_uid(),
                    relationship_type="communicates_with",
                    evidence=ev,
                )
            )

        fps[fp_id] = FunctionalProcess(
            id=fp_id,
            name=f"Process {i}",
            actor_ids=fp_actors,
            data_group_ids=fp_dgs,
            operation_ids=fp_ops,
            evidence=ev,
        )

    return CanonicalFunctionalModel(
        run_id="cfm-test",
        actors=actors,
        functional_processes=fps,
        business_rules=brs,
        data_groups=dgs,
        relationships=rels,
        operations=ops,
        metadata=BuildMetadata(
            run_id="cfm-test", version="1.0", source="test"
        ),
    )


class TestCalculateFromKnownCfm:
    def test_estimate_from_known_cfm(self):
        cfm = _make_cfm(fp_count=3, actors_per_fp=2, ops_per_fp=1)
        result = calculate(cfm, run_id="test-run-001")
        assert isinstance(result, StoryPointMeasurementResult)
        assert result.run_id == "test-run-001"
        assert result.total_story_points > 0
        assert len(result.items) == 3
        for item in result.items:
            assert item.raw_score > 0
            assert item.normalized_value > 0
            assert len(item.factor_breakdown) > 0

    def test_deterministic(self):
        cfm = _make_cfm()
        result1 = calculate(cfm, run_id="det-test")
        result2 = calculate(cfm, run_id="det-test")
        d1 = result1.model_dump()
        d2 = result2.model_dump()
        d1.pop("measured_at", None)
        d2.pop("measured_at", None)
        d1["execution_metadata"]["duration_ms"] = 0
        d2["execution_metadata"]["duration_ms"] = 0
        assert d1 == d2

    def test_empty_cfm(self):
        result = calculate(None, run_id="empty")
        assert result.total_story_points == 0
        assert len(result.items) == 0
        assert result.distribution == {}
        warning_codes = [w.code for w in result.warnings]
        assert "MISSING_CFM" in warning_codes

    def test_cfm_with_no_fps(self):
        cfm = _make_empty_cfm()
        result = calculate(cfm, run_id="no-fps")
        assert result.total_story_points == 0
        assert len(result.items) == 0

    def test_metadata_tracks_counts(self):
        cfm = _make_cfm(fp_count=5, actors_per_fp=1, ops_per_fp=1)
        result = calculate(cfm, run_id="meta")
        assert result.execution_metadata.total_fps_processed == 5
        assert result.execution_metadata.fps_estimated == 5

    def test_distribution_matches_items(self):
        cfm = _make_cfm(fp_count=3, actors_per_fp=1, ops_per_fp=1)
        result = calculate(cfm, run_id="dist")
        expected: dict[int, int] = {}
        for item in result.items:
            expected[item.normalized_value] = (
                expected.get(item.normalized_value, 0) + 1
            )
        assert result.distribution == expected


class TestDuplicateMerge:
    def test_identical_fps_merged(self):
        ev = _make_evidence()
        fp_id = _uid()
        fp = FunctionalProcess(
            id=fp_id,
            name="Duplicate Process",
            actor_ids=[],
            evidence=ev,
        )
        fp2_id = _uid()
        fp2 = FunctionalProcess(
            id=fp2_id,
            name="Duplicate Process",
            actor_ids=[],
            evidence=ev,
        )
        cfm = CanonicalFunctionalModel(
            run_id="dup-test",
            functional_processes={fp_id: fp, fp2_id: fp2},
            metadata=BuildMetadata(
                run_id="dup-test", version="1.0", source="test"
            ),
        )
        result = calculate(cfm, run_id="dup")
        assert result.execution_metadata.fps_estimated == 1
        assert result.execution_metadata.fps_merged_as_duplicates == 1
        assert result.execution_metadata.total_fps_processed == 2


class TestCustomCoefficients:
    def test_custom_coefficients_affect_results(self):
        cfm = _make_cfm(fp_count=1, actors_per_fp=5, ops_per_fp=1)
        default = calculate(cfm, run_id="default")
        custom = calculate(
            cfm,
            run_id="custom",
            coefficients={"business_interactions": 10.0},
        )
        assert custom.total_story_points != default.total_story_points

    def test_custom_thresholds_affect_normalization(self):
        cfm = _make_cfm(fp_count=1, actors_per_fp=1, ops_per_fp=1)
        default = calculate(cfm, run_id="default")
        custom = calculate(
            cfm,
            run_id="custom",
            thresholds=[1000],
            output_values=[1, 100],
        )
        assert custom.total_story_points <= default.total_story_points


class TestAggregation:
    def test_aggregate_summing(self):
        from specmetrics.plugins.measurement.storypoints.models import (
            aggregate,
        )

        cfm = _make_cfm(fp_count=2)
        m1 = calculate(cfm, run_id="m1")
        m2 = calculate(cfm, run_id="m2")
        aggregated = aggregate([m1, m2])
        assert aggregated.total_story_points == (
            m1.total_story_points + m2.total_story_points
        )
        assert len(aggregated.items) == len(m1.items) + len(m2.items)


class TestPerformance:
    @pytest.mark.slow
    def test_performance_500_fps(self):
        cfm = _make_cfm(
            fp_count=500,
            actors_per_fp=2,
            ops_per_fp=2,
            br_per_fp=1,
            rels_per_fp=1,
        )
        start = time.monotonic()
        calculate(cfm, run_id="perf")
        elapsed = time.monotonic() - start
        assert elapsed < 5.0


def _make_empty_cfm() -> CanonicalFunctionalModel:
    return CanonicalFunctionalModel(
        run_id="empty",
        metadata=BuildMetadata(
            run_id="empty", version="1.0", source="test"
        ),
    )
