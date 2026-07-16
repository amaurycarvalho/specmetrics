from __future__ import annotations

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

    @classmethod
    def from_yaml(cls, path: str | Path | None = None) -> ExplanationConfig:
        if path is None:
            base = Path(".specify") / "explanation.yml"
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
        )


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
    ) -> MeasurementExplanation:
        if graph is not None:
            self._tracer.graph = graph

        elements: list[dict[str, Any]] = []
        applied_rules: list[AppliedRule] = []

        if cfm is not None:
            for category_name in ("actors", "functional_processes", "business_rules", "data_groups", "operations"):
                category = cfm.get_elements_by_category(category_name)
                for eid, elem in category.items():
                    evidence_refs = self._tracer.trace_element(eid, cfm=cfm)
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
                        rule_pack_id=run_id,
                        rule_id=rid,
                        rule_type="business_rule",
                        description=rule.description or rule.name,
                        effect="Identified as business rule in CFM",
                    )
                )

        metric = MetricExplanation(
            metric_name="function_count",
            metric_value=len(elements),
            computation_summary=f"Total elements identified in CFM: {len(elements)}",
            elements=[
                ElementContribution(**el) for el in elements
            ],
            applied_rules=applied_rules,
        )

        metrics = [metric]
        if metric_name is not None:
            metrics = [m for m in metrics if m.metric_name == metric_name]
            if not metrics:
                raise ValueError(f"Metric '{metric_name}' not found in run {run_id}")

        explanation = MeasurementExplanation(
            run_id=run_id,
            spec_path=cfm.metadata.run_id if cfm and cfm.metadata else "",
            measured_at=datetime.now(timezone.utc),
            metrics=metrics,
            applied_rules=applied_rules,
            summary=ExplanationSummary(
                total_metrics=len(metrics),
                total_elements=len(elements),
                total_evidence_refs=sum(len(el.evidence) for el in metric.elements),
                total_rules_applied=len(applied_rules),
            ),
        )

        _explanation_store[run_id] = explanation
        return explanation

    def load_explanation(self, run_id: str) -> MeasurementExplanation | None:
        return _explanation_store.get(run_id)

    def compare(
        self,
        baseline_run_id: str,
        comparison_run_id: str,
    ) -> ExplanationComparison:
        baseline = self.load_explanation(baseline_run_id)
        comparison = self.load_explanation(comparison_run_id)

        if baseline is None:
            raise ValueError(f"Baseline run '{baseline_run_id}' not found")
        if comparison is None:
            raise ValueError(f"Comparison run '{comparison_run_id}' not found")

        return compare_explanations(baseline, comparison)
