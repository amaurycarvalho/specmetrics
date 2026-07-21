from __future__ import annotations

from .models import (
    ElementChange,
    ExplanationComparison,
    MeasurementExplanation,
    MetricChange,
)


def _compare_element_fields(be, ce) -> list[dict]:
    changes: list[dict] = []
    for field in ("element_type", "element_label", "complexity", "weight"):
        bv = getattr(be, field, None)
        cv = getattr(ce, field, None)
        if bv != cv:
            changes.append(
                {
                    "field": field,
                    "baseline": bv,
                    "comparison": cv,
                }
            )
    be_evidence_ids = sorted(e.node_id for e in (be.evidence or []))
    ce_evidence_ids = sorted(e.node_id for e in (ce.evidence or []))
    if be_evidence_ids != ce_evidence_ids:
        changes.append(
            {
                "field": "evidence",
                "baseline": be_evidence_ids,
                "comparison": ce_evidence_ids,
            }
        )
    return changes


def compare_explanations(
    baseline: MeasurementExplanation,
    comparison: MeasurementExplanation,
) -> ExplanationComparison:
    baseline_metrics = {m.metric_name: m for m in baseline.metrics}
    comparison_metrics = {m.metric_name: m for m in comparison.metrics}

    all_names = set(baseline_metrics) | set(comparison_metrics)
    added: list[str] = []
    removed: list[str] = []
    changed: list[MetricChange] = []
    unchanged: list[str] = []

    for name in sorted(all_names):
        bm = baseline_metrics.get(name)
        cm = comparison_metrics.get(name)

        if bm is None:
            added.append(name)
        elif cm is None:
            removed.append(name)
        else:
            if bm.metric_value != cm.metric_value:
                baseline_elements = {e.element_id: e for e in bm.elements}
                comparison_elements = {e.element_id: e for e in cm.elements}
                all_elem_ids = set(baseline_elements) | set(comparison_elements)

                elem_changes: list[ElementChange] = []
                for eid in sorted(all_elem_ids):
                    be = baseline_elements.get(eid)
                    ce = comparison_elements.get(eid)
                    if be is None:
                        elem_changes.append(
                            ElementChange(
                                element_id=eid,
                                change_type="added",
                                comparison_state={
                                    "element_type": ce.element_type,
                                    "element_label": ce.element_label,
                                }
                                if ce
                                else {},
                            )
                        )
                    elif ce is None:
                        elem_changes.append(
                            ElementChange(
                                element_id=eid,
                                change_type="removed",
                                baseline_state={
                                    "element_type": be.element_type,
                                    "element_label": be.element_label,
                                },
                            )
                        )
                    else:
                        field_changes = _compare_element_fields(be, ce)
                        if field_changes:
                            change_type = "modified"
                            for fc in field_changes:
                                if fc["field"] in ("complexity", "weight"):
                                    change_type = f"{fc['field']}_changed"
                            elem_changes.append(
                                ElementChange(
                                    element_id=eid,
                                    change_type=change_type,
                                    baseline_state={
                                        fc["field"]: fc["baseline"]
                                        for fc in field_changes
                                    },
                                    comparison_state={
                                        fc["field"]: fc["comparison"]
                                        for fc in field_changes
                                    },
                                )
                            )

                changed.append(
                    MetricChange(
                        metric_name=name,
                        baseline_value=bm.metric_value,
                        comparison_value=cm.metric_value,
                        delta=cm.metric_value - bm.metric_value,
                        changed_elements=elem_changes,
                    )
                )
            else:
                unchanged.append(name)

    summary_parts: list[str] = []
    if changed:
        summary_parts.append(f"{len(changed)} metric(s) changed")
    if added:
        summary_parts.append(f"{len(added)} added")
    if removed:
        summary_parts.append(f"{len(removed)} removed")
    if unchanged:
        summary_parts.append(f"{len(unchanged)} unchanged")
    summary = ", ".join(summary_parts) if summary_parts else "No differences found"

    return ExplanationComparison(
        baseline_run_id=baseline.run_id,
        comparison_run_id=comparison.run_id,
        changed_metrics=changed,
        added_metrics=added,
        removed_metrics=removed,
        unchanged_metrics=unchanged,
        summary=summary,
    )
