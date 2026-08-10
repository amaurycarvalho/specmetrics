"""User story generation from canonical functional model elements."""

from __future__ import annotations

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel, FunctionalProcess


def generate_story(fp: FunctionalProcess, cfm: CanonicalFunctionalModel) -> str:
    """Generate a user story for the given functional process."""
    lines: list[str] = []
    lines.append(f"# User Story: {fp.name}")
    lines.append("")

    _append_actor(fp, cfm, lines)
    _append_operations(fp, cfm, lines)
    _append_business_rules(fp, cfm, lines)
    _append_data_groups(fp, cfm, lines)
    _append_relationships(fp, cfm, lines)

    return "\n".join(lines).strip()


def _append_actor(
    fp: FunctionalProcess, cfm: CanonicalFunctionalModel, lines: list[str]
) -> None:
    actor_names = _resolve_actor_names(fp, cfm)
    if actor_names:
        description = fp.description or fp.name
        lines.append(f"As a {actor_names}, I want to {description}")
        lines.append("")


def _append_operations(
    fp: FunctionalProcess, cfm: CanonicalFunctionalModel, lines: list[str]
) -> None:
    ops = _resolve_operations(fp, cfm)
    if ops:
        lines.append("## Acceptance Criteria:")
        for op_name in ops:
            lines.append(f"- {op_name}")
        lines.append("")


def _append_business_rules(
    fp: FunctionalProcess, cfm: CanonicalFunctionalModel, lines: list[str]
) -> None:
    rules = _resolve_business_rules(fp, cfm)
    if rules:
        lines.append("### Business Rules:")
        for rule_text in rules:
            lines.append(f"- {rule_text}")
        lines.append("")


def _append_data_groups(
    fp: FunctionalProcess, cfm: CanonicalFunctionalModel, lines: list[str]
) -> None:
    dgs = _resolve_data_groups(fp, cfm)
    if dgs:
        lines.append("### Data Groups:")
        for dg_name in dgs:
            lines.append(f"- {dg_name}")
        lines.append("")


def _append_relationships(
    fp: FunctionalProcess, cfm: CanonicalFunctionalModel, lines: list[str]
) -> None:
    rels = _resolve_relationships(fp, cfm)
    if rels:
        lines.append("### Relationships:")
        for rel_text in rels:
            lines.append(f"- {rel_text}")


def _resolve_actor_names(fp: FunctionalProcess, cfm: CanonicalFunctionalModel) -> str:
    names: list[str] = []
    for aid in fp.actor_ids:
        actor = cfm.actors.get(aid)
        if actor:
            names.append(actor.name)
    return ", ".join(names) if names else ""


def _resolve_operations(
    fp: FunctionalProcess, cfm: CanonicalFunctionalModel
) -> list[str]:
    names: list[str] = []
    for oid in fp.operation_ids:
        op = cfm.operations.get(oid)
        if op:
            names.append(op.name)
    return names


def _resolve_business_rules(
    fp: FunctionalProcess, cfm: CanonicalFunctionalModel
) -> list[str]:
    texts: list[str] = []
    for br in cfm.business_rules.values():
        if fp.id in br.related_process_ids:
            texts.append(br.description or br.name)
    return texts


def _resolve_data_groups(
    fp: FunctionalProcess, cfm: CanonicalFunctionalModel
) -> list[str]:
    names: list[str] = []
    for dgid in fp.data_group_ids:
        dg = cfm.data_groups.get(dgid)
        if dg:
            names.append(dg.name)
    return names


def _resolve_relationships(
    fp: FunctionalProcess, cfm: CanonicalFunctionalModel
) -> list[str]:
    texts: list[str] = []
    for rel in cfm.relationships:
        if rel.source_id == fp.id or rel.target_id == fp.id:
            texts.append(f"{rel.relationship_type}: {rel.source_id} → {rel.target_id}")
    return texts
