"""Service for building, persisting, and comparing measurement explanations."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Self

import structlog

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.evidence_graph import EvidenceGraph

from ._metrics import (
    _build_metrics_from_elements,
    _build_metrics_from_measurement_result,
    _build_summary,
    _collect_cfm_elements,
    _collect_metrics,
    _filter_metrics,
    _resolve_spec_path,
)
from .comparison import compare_explanations
from .evidence_tracer import EvidenceTracer
from .models import (
    ExplanationComparison,
    MeasurementExplanation,
)

logger = structlog.get_logger(__name__)

__all__ = [
    "ExplainService",
    "ExplanationConfig",
    "_build_metrics_from_elements",
    "_build_metrics_from_measurement_result",
]

_explanation_store: dict[str, MeasurementExplanation] = {}


@dataclass
class ExplanationConfig:
    """Configuration options for the explanation service."""

    max_evidence_depth: int = 3
    include_low_confidence: bool = False
    min_confidence: float = 0.5
    default_format: str = "text"
    storage_dir: str = ".specmetrics/explanations"

    @classmethod
    def from_yaml(
        cls: type[Self], path: str | Path | None = None
    ) -> ExplanationConfig:
        """Load configuration from a YAML file, falling back to defaults."""
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
            include_low_confidence=cfg.get(
                "include_low_confidence", cls.include_low_confidence
            ),
            min_confidence=cfg.get("min_confidence", cls.min_confidence),
            default_format=cfg.get("default_format", cls.default_format),
            storage_dir=cfg.get("storage_dir", cls.storage_dir),
        )

    @property
    def storage_path(self: Self) -> Path:
        """Return the directory where explanations are persisted."""
        return Path(self.storage_dir)


class ExplainService:
    """Service that builds, persists, and compares explanations."""

    def __init__(
        self: Self,
        tracer: EvidenceTracer | None = None,
        config: ExplanationConfig | None = None,
    ) -> None:
        """Initialize the service with an optional tracer and configuration."""
        self._tracer = tracer or EvidenceTracer()
        self._config = config or ExplanationConfig()

    @property
    def tracer(self: Self) -> EvidenceTracer:
        """Return the evidence tracer used by this service."""
        return self._tracer

    def explain(
        self: Self,
        run_id: str,
        metric_name: str | None = None,
        cfm: CanonicalFunctionalModel | None = None,
        graph: EvidenceGraph | None = None,
        measurement_result: dict[str, Any] | None = None,
        spec_path: str | None = None,
    ) -> MeasurementExplanation:
        """Build and persist a measurement explanation for the given run."""
        if graph is not None:
            self._tracer.graph = graph

        elements, applied_rules = _collect_cfm_elements(cfm, self._tracer)
        metrics = _collect_metrics(measurement_result, elements, applied_rules, cfm)
        metrics = _filter_metrics(metrics, metric_name, run_id)

        explanation = MeasurementExplanation(
            run_id=run_id,
            spec_path=spec_path or _resolve_spec_path(run_id, cfm),
            measured_at=datetime.now(UTC),
            metrics=metrics,
            applied_rules=applied_rules,
            summary=_build_summary(metrics, elements, applied_rules),
        )

        _explanation_store[run_id] = explanation
        self._save_to_disk(run_id, explanation)
        return explanation

    def _save_to_disk(
        self: Self, run_id: str, explanation: MeasurementExplanation
    ) -> None:
        storage_dir = self._config.storage_path
        try:
            storage_dir.mkdir(parents=True, exist_ok=True)
            path = storage_dir / f"{run_id}.json"
            data = explanation.model_dump(mode="json")
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        except OSError as exc:
            logger.warning("explanation_save_failed", run_id=run_id, error=str(exc))

    def load_explanation(
        self: Self, run_id: str, spec_path_hint: str | None = None
    ) -> MeasurementExplanation | None:
        """Load a stored explanation by run id, or return None if missing."""
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
                logger.warning(
                    "explanation_load_failed",
                    run_id=run_id,
                    path=str(path),
                    error=str(exc),
                )
                return None

        return None

    def compare(
        self: Self,
        baseline_run_id: str,
        comparison_run_id: str,
    ) -> ExplanationComparison:
        """Compare two runs and return an explanation comparison."""
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
