from __future__ import annotations

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel, FunctionalProcess


def generate_story(fp: FunctionalProcess, cfm: CanonicalFunctionalModel) -> str:
    lines: list[str] = []
    lines.append(f"# User Story: {fp.name}")
    lines.append("")

    actor_names = _resolve_actor_names(fp, cfm)
    if actor_names:
        description = fp.description or fp.name
        lines.append(
            f"As a {actor_names}, I want to {description}"
        )
        lines.append("")

    ops = _resolve_operations(fp, cfm)
    if ops:
        lines.append("## Acceptance Criteria:")
        for op_name in ops:
            lines.append(f"- {op_name}")
        lines.append("")

    rules = _resolve_business_rules(fp, cfm)
    if rules:
        lines.append("### Business Rules:")
        for rule_text in rules:
            lines.append(f"- {rule_text}")
        lines.append("")

    dgs = _resolve_data_groups(fp, cfm)
    if dgs:
        lines.append("### Data Groups:")
        for dg_name in dgs:
            lines.append(f"- {dg_name}")
        lines.append("")

    rels = _resolve_relationships(fp, cfm)
    if rels:
        lines.append("### Relationships:")
        for rel_text in rels:
            lines.append(f"- {rel_text}")

    return "\n".join(lines).strip()


def _resolve_actor_names(
    fp: FunctionalProcess, cfm: CanonicalFunctionalModel
) -> str:
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
            texts.append(
                f"{rel.relationship_type}: {rel.source_id} → {rel.target_id}"
            )
    return texts
