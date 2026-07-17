from __future__ import annotations

import uuid

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
from specmetrics.plugins.measurement.storypoints.factor_scorer import (
    DEFAULT_FACTOR_COEFFICIENTS,
    FACTOR_NAMES,
    score_all_factors,
    score_factor,
)


def _uid() -> str:
    return str(uuid.uuid4())


def _make_evidence() -> EvidenceRef:
    return EvidenceRef(
        graph_node_id="gn-001", document_id="doc-001", text="evidence"
    )


def _make_cfm_with_fp(
    actor_count: int = 0,
    data_group_count: int = 0,
    operation_count: int = 0,
    business_rule_count: int = 0,
    relationship_count: int = 0,
    has_exception: bool = False,
) -> tuple[CanonicalFunctionalModel, str]:
    ev = _make_evidence()
    fp_id = _uid()

    actors = {}
    data_groups = {}
    operations = {}
    business_rules = {}
    relationships = []

    for i in range(actor_count):
        aid = _uid()
        actors[aid] = Actor(id=aid, name=f"Actor {i}", evidence=ev)

    for i in range(data_group_count):
        dgid = _uid()
        data_groups[dgid] = DataGroup(
            id=dgid, name=f"DG {i}", evidence=ev
        )

    for i in range(operation_count):
        oid = _uid()
        meta = {"type": "exception"} if has_exception and i == 0 else {}
        operations[oid] = Operation(
            id=oid,
            name=f"Op {i}",
            parent_process_id=fp_id,
            evidence=ev,
            metadata=meta,
        )

    for i in range(business_rule_count):
        brid = _uid()
        business_rules[brid] = BusinessRule(
            id=brid,
            name=f"BR {i}",
            related_process_ids=[fp_id],
            evidence=ev,
        )

    for i in range(relationship_count):
        rel_id = _uid()
        relationships.append(
            Relationship(
                id=rel_id,
                source_id=fp_id,
                target_id=_uid(),
                relationship_type="communicates_with",
                evidence=ev,
            )
        )

    fp = FunctionalProcess(
        id=fp_id,
        name="Test Process",
        actor_ids=list(actors.keys()),
        data_group_ids=list(data_groups.keys()),
        operation_ids=list(operations.keys()),
        evidence=ev,
    )
    functional_processes = {fp_id: fp}

    cfm = CanonicalFunctionalModel(
        run_id="test",
        actors=actors,
        functional_processes=functional_processes,
        business_rules=business_rules,
        data_groups=data_groups,
        relationships=relationships,
        operations=operations,
        metadata=BuildMetadata(run_id="test", version="1.0", source="test"),
    )

    return cfm, fp_id


def _make_empty_cfm() -> CanonicalFunctionalModel:
    return CanonicalFunctionalModel(
        run_id="empty",
        metadata=BuildMetadata(
            run_id="empty", version="1.0", source="test"
        ),
    )


class TestBusinessInteractions:
    def test_counts_actors(self):
        cfm, fp_id = _make_cfm_with_fp(actor_count=3)
        fp = cfm.functional_processes[fp_id]
        score = score_factor("business_interactions", fp_id, cfm, fp)
        assert score == 3.0

    def test_zero_when_no_actors(self):
        cfm, fp_id = _make_cfm_with_fp(actor_count=0)
        fp = cfm.functional_processes[fp_id]
        score = score_factor("business_interactions", fp_id, cfm, fp)
        assert score == 0.0


class TestLogicalInformation:
    def test_counts_data_groups_and_operations(self):
        cfm, fp_id = _make_cfm_with_fp(
            data_group_count=2, operation_count=3
        )
        fp = cfm.functional_processes[fp_id]
        score = score_factor("logical_information", fp_id, cfm, fp)
        assert score == 5.0

    def test_zero_when_none(self):
        cfm, fp_id = _make_cfm_with_fp()
        fp = cfm.functional_processes[fp_id]
        score = score_factor("logical_information", fp_id, cfm, fp)
        assert score == 0.0


class TestExternalIntegrations:
    def test_counts_communicates_with_relationships(self):
        cfm, fp_id = _make_cfm_with_fp(relationship_count=2)
        fp = cfm.functional_processes[fp_id]
        score = score_factor("external_integrations", fp_id, cfm, fp)
        assert score == 2.0

    def test_zero_when_no_relationships(self):
        cfm, fp_id = _make_cfm_with_fp()
        fp = cfm.functional_processes[fp_id]
        score = score_factor("external_integrations", fp_id, cfm, fp)
        assert score == 0.0


class TestBusinessRuleDensity:
    def test_counts_related_business_rules(self):
        cfm, fp_id = _make_cfm_with_fp(business_rule_count=4)
        fp = cfm.functional_processes[fp_id]
        score = score_factor("business_rule_density", fp_id, cfm, fp)
        assert score == 4.0

    def test_zero_when_no_rules(self):
        cfm, fp_id = _make_cfm_with_fp()
        fp = cfm.functional_processes[fp_id]
        score = score_factor("business_rule_density", fp_id, cfm, fp)
        assert score == 0.0


class TestWorkflowBreadth:
    def test_counts_operations(self):
        cfm, fp_id = _make_cfm_with_fp(operation_count=5)
        fp = cfm.functional_processes[fp_id]
        score = score_factor("workflow_breadth", fp_id, cfm, fp)
        assert score == 5.0

    def test_zero_when_no_operations(self):
        cfm, fp_id = _make_cfm_with_fp()
        fp = cfm.functional_processes[fp_id]
        score = score_factor("workflow_breadth", fp_id, cfm, fp)
        assert score == 0.0


class TestExceptionHandling:
    def test_detects_exception_operation(self):
        cfm, fp_id = _make_cfm_with_fp(
            operation_count=1, has_exception=True
        )
        fp = cfm.functional_processes[fp_id]
        score = score_factor("exception_handling", fp_id, cfm, fp)
        assert score == 1.0

    def test_zero_when_no_exception(self):
        cfm, fp_id = _make_cfm_with_fp(
            operation_count=2, has_exception=False
        )
        fp = cfm.functional_processes[fp_id]
        score = score_factor("exception_handling", fp_id, cfm, fp)
        assert score == 0.0


class TestScoreAllFactors:
    def test_default_coefficients_applied(self):
        cfm, fp_id = _make_cfm_with_fp(
            actor_count=1,
            data_group_count=1,
            operation_count=1,
            business_rule_count=1,
        )
        fp = cfm.functional_processes[fp_id]
        factors = score_all_factors(fp_id, cfm, fp)
        assert "business_interactions" in factors
        assert "logical_information" in factors
        assert "workflow_breadth" in factors
        assert factors["business_interactions"] == 1.0 * DEFAULT_FACTOR_COEFFICIENTS["business_interactions"]

    def test_custom_coefficients(self):
        cfm, fp_id = _make_cfm_with_fp(
            actor_count=2,
        )
        fp = cfm.functional_processes[fp_id]
        factors = score_all_factors(
            fp_id, cfm, fp, coefficients={"business_interactions": 3.0}
        )
        assert factors["business_interactions"] == 6.0

    def test_all_factor_names_present(self):
        cfm, fp_id = _make_cfm_with_fp(
            actor_count=1, data_group_count=1, operation_count=1
        )
        fp = cfm.functional_processes[fp_id]
        factors = score_all_factors(fp_id, cfm, fp)
        for name in FACTOR_NAMES:
            assert name in factors


class TestScoreAllFactorsEmpty:
    def test_empty_cfm_returns_zero(self):
        cfm = _make_empty_cfm()
        fp_id = _uid()
        fp = FunctionalProcess(
            id=fp_id,
            name="dummy",
            evidence=_make_evidence(),
        )
        cfm.functional_processes[fp_id] = fp
        factors = score_all_factors(fp_id, cfm, fp)
        assert all(v == 0.0 for v in factors.values())
