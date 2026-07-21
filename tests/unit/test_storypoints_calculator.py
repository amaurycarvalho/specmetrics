from __future__ import annotations

import uuid
import time

import pytest

from specmetrics.kernel.cfm.model import (
    Actor,
    BusinessRule,
    CanonicalFunctionalModel,
    DataGroup,
    EvidenceRef as CfmEvidenceRef,
    FunctionalProcess,
    Operation,
    Relationship,
    BuildMetadata as CfmBuildMeta,
)
from specmetrics.kernel.csm.model import (
    AcceptanceCriterion,
    Assumption,
    CanonicalSpecificationModel,
    Decision,
    EvidenceRef as CsmEvidenceRef,
    BuildMetadata as CsmBuildMeta,
)
from specmetrics.plugins.measurement.storypoints.calculator import calculate
from specmetrics.plugins.measurement.storypoints.models import (
    StoryPointMeasurementResult,
)
from specmetrics.plugins.measurement.storypoints.calibrator import (
    StoryPointsCalibrationProfile,
)
from specmetrics.plugins.measurement.storypoints.token_counter import (
    count_tokens_for_element,
)


def _uid() -> str:
    return str(uuid.uuid4())


def _make_evidence(text: str = "evidence") -> CfmEvidenceRef:
    return CfmEvidenceRef(graph_node_id="gn-001", document_id="doc-001", text=text)


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
        metadata=CfmBuildMeta(run_id="cfm-test", version="1.0", source="test"),
    )


class TestCalculateFromKnownCfm:
    def test_estimate_from_known_cfm(self):
        cfm = _make_cfm(fp_count=3, actors_per_fp=2, ops_per_fp=1)
        result = calculate(cfm, run_id="test-run-001")
        assert isinstance(result, StoryPointMeasurementResult)
        assert result.run_id == "test-run-001"
        assert result.total_story_points > 0
        fp_items = [i for i in result.items if i.element_type == "functional_process"]
        assert len(fp_items) == 3
        for item in fp_items:
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
            expected[item.normalized_value] = expected.get(item.normalized_value, 0) + 1
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
            metadata=CfmBuildMeta(run_id="dup-test", version="1.0", source="test"),
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
        assert custom.total_raw_score != default.total_raw_score

    def test_custom_calibration_affects_ranking(self):
        cfm = _make_cfm(fp_count=1, actors_per_fp=0, ops_per_fp=0)
        from specmetrics.plugins.measurement.storypoints.calibrator import (
            StoryPointsCalibrationProfile,
        )
        cal_custom = StoryPointsCalibrationProfile(
            fibonacci_scale=[1, 5, 10, 20, 50, 100],
        )
        result = calculate(
            cfm,
            run_id="custom",
            calibration=cal_custom,
        )
        assert result.total_story_points > 0
        assert len(result.items) > 0


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


def _make_cfm_with_descriptions(
    fp_specs: list[tuple[str, str, str]],
) -> CanonicalFunctionalModel:
    actors: dict[str, Actor] = {}
    fps: dict[str, FunctionalProcess] = {}
    dgs: dict[str, DataGroup] = {}
    ops: dict[str, Operation] = {}

    for i, (fp_id_str, name, description) in enumerate(fp_specs):
        ev = _make_evidence(text=f"evidence {i}")
        fp_id = fp_id_str or _uid()
        fp_actors = []
        for j in range(2):
            aid = _uid()
            actors[aid] = Actor(id=aid, name=f"Actor {i}-{j}", evidence=ev)
            fp_actors.append(aid)

        dgid = _uid()
        dgs[dgid] = DataGroup(id=dgid, name=f"DG {i}", evidence=ev)

        oid = _uid()
        ops[oid] = Operation(
            id=oid,
            name=f"Op {i}",
            parent_process_id=fp_id,
            evidence=ev,
        )

        fps[fp_id] = FunctionalProcess(
            id=fp_id,
            name=name,
            description=description,
            actor_ids=fp_actors,
            data_group_ids=[dgid],
            operation_ids=[oid],
            evidence=ev,
        )

    return CanonicalFunctionalModel(
        run_id="cfm-desc-test",
        actors=actors,
        functional_processes=fps,
        data_groups=dgs,
        operations=ops,
        metadata=CfmBuildMeta(run_id="cfm-desc-test", version="1.0", source="test"),
    )


class TestUserStory1ContentAwareEstimation:
    def test_different_descriptions_produce_different_raw_scores(self):
        short_desc = "x"
        long_desc = "word " * 100
        cfm = _make_cfm_with_descriptions([
            ("fp-001", "Process A", short_desc),
            ("fp-002", "Process B", long_desc),
        ])
        result = calculate(cfm, run_id="us1-test-1")
        fp_items = [i for i in result.items if i.element_type == "functional_process"]
        assert len(fp_items) == 2
        item_short = next(i for i in fp_items if i.element_id == "fp-001")
        item_long = next(i for i in result.items if i.element_id == "fp-002")
        structural_short = item_short.structural_score
        structural_long = item_long.structural_score
        assert structural_short == structural_long
        tokens_short = count_tokens_for_element("Process A", short_desc)
        tokens_long = count_tokens_for_element("Process B", long_desc)
        assert tokens_long > tokens_short
        expected_diff = (tokens_long - tokens_short) * 0.1
        assert abs(item_long.raw_score - item_short.raw_score - expected_diff) < 0.01

    def test_exact_500_vs_100_token_diff(self):
        desc_100 = ("test word " * 50).strip()
        desc_500 = ("test word " * 250).strip()
        cfm = _make_cfm_with_descriptions([
            ("fp-001", "FP1", desc_100),
            ("fp-002", "FP2", desc_500),
        ])
        result = calculate(cfm, run_id="us1-ac1")
        fp_items = [i for i in result.items if i.element_type == "functional_process"]
        assert len(fp_items) == 2
        item_small = next(i for i in fp_items if i.element_id == "fp-001")
        item_large = next(i for i in fp_items if i.element_id == "fp-002")
        t_small = count_tokens_for_element("FP1", desc_100)
        t_large = count_tokens_for_element("FP2", desc_500)
        assert t_large - t_small == 400
        expected_diff = 400 * 0.1
        assert abs(item_large.raw_score - item_small.raw_score - expected_diff) < 0.01

    def test_zero_content_multiplier_matches_structural_only(self):
        cfm = _make_cfm_with_descriptions([
            ("fp-001", "Test FP", "some description text here for testing"),
        ])
        cal = StoryPointsCalibrationProfile(content_multiplier=0.0)
        result = calculate(cfm, run_id="us1-test-2", calibration=cal)
        item = result.items[0]
        assert item.content_score == 0.0
        assert item.content_tokens > 0
        assert abs(item.raw_score - item.structural_score) < 0.001

    def test_empty_name_and_description_has_zero_content(self):
        cfm = _make_cfm_with_descriptions([
            ("fp-001", "", ""),
        ])
        result = calculate(cfm, run_id="us1-test-3")
        item = result.items[0]
        assert item.content_tokens == 0
        assert item.content_score == 0.0
        assert item.structural_score > 0
        assert abs(item.raw_score - item.structural_score) < 0.001


def _uid_csm() -> str:
    return str(uuid.uuid4())


def _make_csm() -> CanonicalSpecificationModel:
    ev = CsmEvidenceRef(graph_node_id="gn-csm", document_id="doc-csm", text="csm evidence")
    dec1_id = _uid_csm()
    dec2_id = _uid_csm()
    asm1_id = _uid_csm()
    ac1_id = _uid_csm()
    return CanonicalSpecificationModel(
        run_id="csm-test",
        decisions={
            dec1_id: Decision(
                id=dec1_id,
                description="System shall use OAuth2",
                evidence_references=[ev],
            ),
            dec2_id: Decision(
                id=dec2_id,
                description="Use PostgreSQL for persistence",
                evidence_references=[ev],
            ),
        },
        assumptions={
            asm1_id: Assumption(
                id=asm1_id,
                description="Network latency < 100ms",
                evidence_references=[ev],
            ),
        },
        acceptance_criteria={
            ac1_id: AcceptanceCriterion(
                id=ac1_id,
                description="User can login within 2 seconds",
                evidence_references=[ev],
            ),
        },
        metadata=CsmBuildMeta(run_id="csm-test", version="1.0", source="test"),
    )


def _make_csm_only() -> CanonicalSpecificationModel:
    csm = _make_csm()
    return CanonicalSpecificationModel(
        run_id="csm-only",
        decisions=csm.decisions,
        assumptions=csm.assumptions,
        metadata=CsmBuildMeta(run_id="csm-only", version="1.0", source="test"),
    )


class TestUserStory2CompleteScope:
    def test_csm_elements_contribute_to_specification_effort(self):
        cfm = _make_cfm(fp_count=1, actors_per_fp=1, ops_per_fp=1)
        csm = _make_csm()
        result = calculate(cfm, run_id="us2-test-1", csm=csm)
        csm_items = [i for i in result.items if i.source_model == "CSM"]
        assert len(csm_items) >= 4
        for item in csm_items:
            assert item.base_weight is not None
            assert item.factor_breakdown == {}
        assert result.specification_effort_total > 0

    def test_non_fp_cfm_elements_contribute_to_implementation_effort(self):
        cfm = _make_cfm_with_descriptions([
            ("fp-001", "FP", "desc"),
        ])
        result = calculate(cfm, run_id="us2-test-2")
        non_fp_cfm = [i for i in result.items if i.source_model == "CFM" and i.element_type != "functional_process"]
        assert len(non_fp_cfm) > 0
        for item in non_fp_cfm:
            assert item.base_weight is not None

    def test_fp_only_spec_works_as_before(self):
        cfm = _make_cfm(fp_count=2, actors_per_fp=1, ops_per_fp=1)
        result = calculate(cfm, run_id="us2-test-3")
        fp_items = [i for i in result.items if i.element_type == "functional_process"]
        assert len(fp_items) == 2
        assert result.total_raw_score > 0

    def test_csm_only_produces_no_fps_warning(self):
        csm = _make_csm_only()
        empty_cfm = CanonicalFunctionalModel(
            run_id="empty",
            metadata=CfmBuildMeta(run_id="empty", version="1.0", source="test"),
        )
        result = calculate(empty_cfm, run_id="us2-test-4", csm=csm)
        assert result.total_raw_score > 0
        csm_items = [i for i in result.items if i.source_model == "CSM"]
        assert len(csm_items) > 0
        warning_codes = [w.code for w in result.warnings]
        assert "NO_FPS_FOUND" in warning_codes


class TestUserStory3CrossSpecPayload:
    def test_effort_totals_sum_to_total_raw(self):
        cfm = _make_cfm(fp_count=2, actors_per_fp=1, ops_per_fp=1)
        csm = _make_csm()
        result = calculate(cfm, run_id="us3-test-1", csm=csm)
        assert abs(
            result.specification_effort_total + result.implementation_effort_total
            - result.total_raw_score
        ) < 0.001

    def test_content_tokens_by_type_populated(self):
        cfm = _make_cfm_with_descriptions([
            ("fp-001", "Process A", "some description here"),
        ])
        result = calculate(cfm, run_id="us3-test-2")
        assert len(result.content_tokens_by_type) > 0
        assert "functional_process" in result.content_tokens_by_type


def _make_empty_cfm() -> CanonicalFunctionalModel:
    return CanonicalFunctionalModel(
        run_id="empty",
        metadata=CfmBuildMeta(run_id="empty", version="1.0", source="test"),
    )
