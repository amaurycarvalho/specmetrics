from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.evidence_graph import EvidenceGraph

from .comparison import compare_explanations
from .evidence_tracer import EvidenceTracer
from .models import (
    AppliedRule,
    ElementContribution,
    ExplanationComparison,
    ExplanationSummary,
    MeasurementExplanation,
    MetricExplanation,
)

logger = structlog.get_logger(__name__)

_explanation_store: dict[str, MeasurementExplanation] = {}


@dataclass
class ExplanationConfig:
    max_evidence_depth: int = 3
    include_low_confidence: bool = False
    min_confidence: float = 0.5
    default_format: str = "text"
    storage_dir: str = ".specmetrics/explanations"

    @classmethod
    def from_yaml(cls, path: str | Path | None = None) -> ExplanationConfig:
        if path is None:
            base = Path(".specmetrics") / "explanations" / "explanation.yml"
            if base.exists():
                path = base
            else:
                return cls()
        import yaml

        path = Path(path)
        if not path.exists():
            return cls()
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        cfg = data.get("explanation", {})
        return cls(
            max_evidence_depth=cfg.get("max_evidence_depth", cls.max_evidence_depth),
            include_low_confidence=cfg.get("include_low_confidence", cls.include_low_confidence),
            min_confidence=cfg.get("min_confidence", cls.min_confidence),
            default_format=cfg.get("default_format", cls.default_format),
            storage_dir=cfg.get("storage_dir", cls.storage_dir),
        )

    @property
    def storage_path(self) -> Path:
        return Path(self.storage_dir)


def _build_metrics_from_elements(
    elements: list[dict[str, Any]],
    applied_rules: list[AppliedRule],
    cfm: CanonicalFunctionalModel | None,
) -> list[MetricExplanation]:
    type_counts: dict[str, int] = {}
    for el in elements:
        t = el["element_type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    metrics: list[MetricExplanation] = [
        MetricExplanation(
            metric_name="function_count",
            metric_value=len(elements),
            computation_summary=f"Total elements identified: {len(elements)}",
            elements=[ElementContribution(**el) for el in elements],
            applied_rules=applied_rules,
        ),
    ]

    for elem_type, count in sorted(type_counts.items()):
        type_elements = [el for el in elements if el["element_type"] == elem_type]
        metrics.append(
            MetricExplanation(
                metric_name=f"{elem_type}_count",
                metric_value=count,
                computation_summary=f"Total {elem_type} elements: {count}",
                elements=[ElementContribution(**el) for el in type_elements],
                applied_rules=applied_rules,
            )
        )

    return metrics


def _build_metrics_from_measurement_result(
    measurement_result: dict[str, Any],
    elements: list[dict[str, Any]],
    applied_rules: list[AppliedRule],
) -> list[MetricExplanation]:
    metrics: list[MetricExplanation] = []

    total_fp = measurement_result.get("total_function_points", 0)
    if total_fp is not None:
        metrics.append(
            MetricExplanation(
                metric_name="functional_size",
                metric_value=total_fp,
                computation_summary=f"Total function points: {total_fp}",
                elements=[ElementContribution(**el) for el in elements],
                applied_rules=applied_rules,
            )
        )

    breakdown = measurement_result.get("breakdown", {})
    for ft, bd in breakdown.items():
        metrics.append(
            MetricExplanation(
                metric_name=f"{ft}_count",
                metric_value=bd.get("count", 0),
                computation_summary=f"Total {ft} elements: {bd.get('count', 0)} (UFP: {bd.get('total_ufp', 0)})",
                elements=[ElementContribution(**el) for el in elements if el["element_type"] == ft],
                applied_rules=applied_rules,
            )
        )

    complexity_dist = measurement_result.get("complexity_distribution", [])
    for cd in complexity_dist:
        fn_type = cd.get("function_type", "unknown")
        comp = cd.get("complexity", "unknown")
        metrics.append(
            MetricExplanation(
                metric_name=f"{fn_type}_{comp}_count",
                metric_value=cd.get("count", 0),
                computation_summary=f"Total {fn_type} ({comp}): {cd.get('count', 0)}",
                elements=[],
                applied_rules=applied_rules,
            )
        )

    return metrics


def _collect_cfm_elements(
    cfm: CanonicalFunctionalModel | None,
    tracer: EvidenceTracer,
) -> tuple[list[dict[str, Any]], list[AppliedRule]]:
    elements: list[dict[str, Any]] = []
    applied_rules: list[AppliedRule] = []

    if cfm is None:
        return elements, applied_rules

    for category_name in ("actors", "functional_processes", "business_rules", "data_groups", "operations"):
        category = cfm.get_elements_by_category(category_name)
        for eid, elem in category.items():
            evidence_refs = tracer.trace_element(eid, cfm=cfm)
            elements.append({
                "element_id": eid,
                "element_type": category_name,
                "element_label": getattr(elem, "name", eid),
                "complexity": None,
                "weight": None,
                "evidence": evidence_refs,
                "applied_rules": [],
            })

    for rid, rule in cfm.business_rules.items():
        applied_rules.append(
            AppliedRule(
                rule_pack_id=str(getattr(cfm, "run_id", rid)),
                rule_id=rid,
                rule_type="business_rule",
                description=rule.description or rule.name,
                effect="Identified as business rule in CFM",
            )
        )

    return elements, applied_rules


class ExplainService:
    def __init__(
        self,
        tracer: EvidenceTracer | None = None,
        config: ExplanationConfig | None = None,
    ):
        self._tracer = tracer or EvidenceTracer()
        self._config = config or ExplanationConfig()

    @property
    def tracer(self) -> EvidenceTracer:
        return self._tracer

    def explain(
        self,
        run_id: str,
        metric_name: str | None = None,
        cfm: CanonicalFunctionalModel | None = None,
        graph: EvidenceGraph | None = None,
        measurement_result: dict[str, Any] | None = None,
        spec_path: str | None = None,
    ) -> MeasurementExplanation:
        if graph is not None:
            self._tracer.graph = graph

        elements, applied_rules = _collect_cfm_elements(cfm, self._tracer)

        if measurement_result:
            metrics = _build_metrics_from_measurement_result(measurement_result, elements, applied_rules)
        else:
            metrics = _build_metrics_from_elements(elements, applied_rules, cfm)

        if metric_name is not None:
            metrics = [m for m in metrics if m.metric_name == metric_name]
            if not metrics:
                raise ValueError(f"Metric '{metric_name}' not found in run {run_id}")

        if not cfm:
            gaps: list[str] = []
            gaps.append("CFM not available — element-level detail omitted")
        else:
            gaps = []

        if graph is None:
            gaps.append("Evidence graph not available — evidence references may be incomplete")

        explanation = MeasurementExplanation(
            run_id=run_id,
            spec_path=spec_path or (cfm.metadata.run_id if cfm and cfm.metadata else run_id),
            measured_at=datetime.now(timezone.utc),
            metrics=metrics,
            applied_rules=applied_rules,
            summary=ExplanationSummary(
                total_metrics=len(metrics),
                total_elements=len(elements),
                total_evidence_refs=sum(len(el.evidence) for el in metrics[0].elements) if metrics else 0,
                total_rules_applied=len(applied_rules),
            ),
        )

        _explanation_store[run_id] = explanation
        self._save_to_disk(run_id, explanation)
        return explanation

    def _save_to_disk(self, run_id: str, explanation: MeasurementExplanation) -> None:
        storage_dir = self._config.storage_path
        try:
            storage_dir.mkdir(parents=True, exist_ok=True)
            path = storage_dir / f"{run_id}.json"
            data = explanation.model_dump(mode="json")
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        except OSError as exc:
            logger.warning("explanation_save_failed", run_id=run_id, error=str(exc))

    def load_explanation(self, run_id: str, spec_path_hint: str | None = None) -> MeasurementExplanation | None:
        cached = _explanation_store.get(run_id)
        if cached is not None:
            return cached

        path = self._config.storage_path / f"{run_id}.json"
        if path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                explanation = MeasurementExplanation.model_validate(data)
                _explanation_store[run_id] = explanation
                return explanation
            except (json.JSONDecodeError, KeyError, ValueError) as exc:
                logger.warning("explanation_load_failed", run_id=run_id, path=str(path), error=str(exc))
                return None

        return None

    def compare(
        self,
        baseline_run_id: str,
        comparison_run_id: str,
    ) -> ExplanationComparison:
        baseline = self.load_explanation(baseline_run_id)
        comparison = self.load_explanation(comparison_run_id)

        if baseline is None and comparison is None:
            return ExplanationComparison(
                baseline_run_id=baseline_run_id,
                comparison_run_id=comparison_run_id,
                changed_metrics=[],
                added_metrics=[],
                removed_metrics=[],
                unchanged_metrics=[],
                summary=f"Both runs '{baseline_run_id}' and '{comparison_run_id}' not found",
            )

        if baseline is None:
            return ExplanationComparison(
                baseline_run_id=baseline_run_id,
                comparison_run_id=comparison_run_id,
                changed_metrics=[],
                added_metrics=[],
                removed_metrics=[],
                unchanged_metrics=[],
                summary=f"Baseline run '{baseline_run_id}' not found — comparison unavailable",
            )

        if comparison is None:
            return ExplanationComparison(
                baseline_run_id=baseline_run_id,
                comparison_run_id=comparison_run_id,
                changed_metrics=[],
                added_metrics=[],
                removed_metrics=[],
                unchanged_metrics=[],
                summary=f"Comparison run '{comparison_run_id}' not found — comparison unavailable",
            )

        return compare_explanations(baseline, comparison)
