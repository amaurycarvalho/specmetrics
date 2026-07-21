from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


import structlog

from specmetrics.kernel.adapter_registry import AdapterRegistry
from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.csm.model import CanonicalSpecificationModel
from specmetrics.kernel.diagnostics import StageStatus as KernelStageStatus
from specmetrics.kernel.events import EventType
from specmetrics.kernel.exceptions import PipelineError
from specmetrics.kernel.handler_registry import HandlerRegistry
from specmetrics.kernel.llm_gateway import LLMGateway, LLMGatewayConfig
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.kernel.pipeline_engine import CANONICAL_EVENT_ORDER, PipelineEngine
from specmetrics.kernel.plugin_discovery import load_plugins
from specmetrics.kernel.plugin_registry import PluginRegistry
from specmetrics.kernel.plugin_validation import PluginValidator

from .enums import (
    OutputFormat,
    PipelineStatus,
    StageExecutionStatus,
    StageName,
)
from specmetrics.infrastructure.config.loader import ConfigurationSystem
from specmetrics.cli.output_models import (
    ErrorRecord,
    MeasureMetadata,
    MeasureOutput,
    MetricResult as OutputMetricResult,
    StageInfo as OutputStageInfo,
)

from .models import (
    METRIC_NAME_MAP,
    ErrorOutputItem,
    MeasurementResult,
    MetricOutputItem,
    PipelineRequest,
    PipelineResult,
    PluginInfo,
    StageOutputItem,
    StageResult,
    VersionInfo,
)


_TRUNCATE_TEXT_LENGTH = 200


def _truncate_text(
    text: str | None, max_len: int = _TRUNCATE_TEXT_LENGTH
) -> str | None:
    if text is None:
        return None
    return text[:max_len] if len(text) > max_len else text


def _truncate_entities(
    entities: list[dict],
    max_per_stage: int,
    per_category: bool = False,
) -> list[dict]:
    if len(entities) <= max_per_stage:
        return entities
    logger.info(
        "entities_truncated",
        total=len(entities),
        limit=max_per_stage,
        per_category=per_category,
    )
    if per_category:
        truncated: list[dict] = []
        categories: dict[str, list[dict]] = {}
        for e in entities:
            cat = e.get("type", "_other")
            categories.setdefault(cat, []).append(e)
        for cat_list in categories.values():
            truncated.extend(cat_list[:max_per_stage])
        truncated.append({"_truncated": True, "_total_count": len(entities)})
        return truncated
    truncated = entities[:max_per_stage]
    truncated.append({"_truncated": True, "_total_count": len(entities)})
    return truncated


logger = structlog.get_logger(__name__)


def _serialize_stage_data(
    result: PipelineResult,
    max_entities_per_stage: int = 5000,
) -> dict[str, list[dict]]:
    stages: dict[str, list[dict]] = {}
    csm_cfm_stages = {"csm", "cfm"}
    for sd in result.stage_details:
        entry: dict = {
            "name": sd.name,
            "count": sd.count,
            "count_type": sd.count_type,
            "duration_ms": sd.duration_ms,
        }
        raw_entities = result.stage_entities.get(sd.name, [])
        if raw_entities:
            per_category = sd.name in csm_cfm_stages
            entry["entities"] = _truncate_entities(
                raw_entities, max_entities_per_stage, per_category=per_category
            )
        else:
            entry["entities"] = []
        stages[sd.name] = [entry]
    return stages


def save_run_artifacts(
    project_path: Path,
    measure_id: str,
    result: PipelineResult,
    max_entities_per_stage: int = 5000,
) -> Path:
    runs_dir = project_path / ".specmetrics" / "runs" / measure_id
    runs_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "id": measure_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sdd_framework": (
            result._framework_detected
            if getattr(result, "_framework_detected", None)
            and isinstance(result._framework_detected, str)
            else "unknown"
        ),
        "llm": (
            {"provider": result.llm_provider, "model": result.llm_model}
            if result.llm_provider and result.llm_provider != "none"
            else {"provider": "none"}
        ),
        "project_path": str(result.project_path or project_path),
    }
    (runs_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

    stages = _serialize_stage_data(
        result, max_entities_per_stage=max_entities_per_stage
    )
    for stage_name, entries in stages.items():
        (runs_dir / f"{stage_name}.json").write_text(json.dumps(entries, indent=2))

    logger.info("run_artifacts_saved", path=str(runs_dir), stages=list(stages.keys()))
    return runs_dir


def read_run_artifacts(run_dir: Path) -> dict:
    artifacts: dict = {}
    metadata_file = run_dir / "metadata.json"
    if metadata_file.exists():
        artifacts["metadata"] = json.loads(metadata_file.read_text())
    for stage_file in sorted(run_dir.glob("*.json")):
        if stage_file.name in ("metadata.json", "metrics.json"):
            continue
        artifacts[stage_file.stem] = json.loads(stage_file.read_text())
    return artifacts


_STAGE_NAME_TO_EVENT: dict[StageName, EventType] = {
    StageName.DISCOVER: EventType.REPOSITORY_LOADED,
    StageName.EXTRACT: EventType.SEMANTIC_EXTRACTION_COMPLETED,
    StageName.GRAPH: EventType.EVIDENCE_GRAPH_BUILT,
    StageName.CSM: EventType.CANONICAL_SPECIFICATION_MODEL_BUILT,
    StageName.CFM: EventType.CANONICAL_MODEL_BUILT,
    StageName.RULE: EventType.RULE_PACK_APPLIED,
    StageName.MEASURE: EventType.MEASUREMENT_COMPLETED,
    StageName.EXPORT: EventType.EXPORT_COMPLETED,
}

_STAGE_NAME_TO_HANDLER_NAMES: dict[str, list[str]] = {
    "discover": ["discovery"],
    "extract": ["semantic_extraction"],
    "graph": ["evidence_graph"],
    "csm": ["canonical_spec_model"],
    "cfm": ["canonical_model"],
    "rule": ["Rule Pack Engine"],
    "measure": [
        "FPA Measurement",
        "SFP Measurement",
        "SNAP Measurement",
        "Story Points Measurement",
        "Token Points Measurement",
        "Cognitive Points Measurement",
        "BCP Measurement",
    ],
    "export": [],
}


def _stage_name_from_event(event_type: EventType) -> str:
    for stage_name, et in _STAGE_NAME_TO_EVENT.items():
        if et == event_type:
            return stage_name.value
    return event_type.value


def _resolve_event_order(
    stages: list[StageName] | None,
    from_stage: StageName | None,
) -> list[EventType]:
    if stages is not None:
        return [_STAGE_NAME_TO_EVENT[s] for s in stages]
    if from_stage is not None:
        start_event = _STAGE_NAME_TO_EVENT[from_stage]
        started = False
        result: list[EventType] = []
        for et in CANONICAL_EVENT_ORDER:
            if et == start_event:
                started = True
            if started:
                result.append(et)
        return result
    return list(CANONICAL_EVENT_ORDER)


class PipelineOrchestrator:
    """Shared pipeline orchestrator consumed by both CLI and MCP interfaces.

    Discovers plugins, executes the pipeline via Kernel PipelineEngine,
    and returns structured PipelineResult. Ensures behavioral consistency
    across all interaction mechanisms.
    """

    def __init__(self) -> None:
        self._registry = PluginRegistry()
        self._handler_registry = HandlerRegistry()
        self._plugin_validator = PluginValidator()
        self._config_system: ConfigurationSystem | None = None

    def set_config_system(self, config_system: ConfigurationSystem) -> None:
        self._config_system = config_system

    def discover_plugins(self, metrics_filter: list[str] | None = None) -> None:
        self._registry = load_plugins(
            registry=self._registry,
            validator=self._plugin_validator,
        )
        self._registry.install_handlers(
            self._handler_registry, metrics_filter=metrics_filter
        )
        if self._config_system is not None:
            for desc in self._registry.list_plugins():
                factory = desc.metadata.handler_factory
                if factory is not None:
                    try:
                        handler = factory()
                        schema_method = getattr(handler, "config_schema", None)
                        if schema_method is not None and callable(schema_method):
                            schema = schema_method()
                            if schema is not None:
                                self._config_system.register_plugin_schema(
                                    desc.metadata.id,
                                    schema,
                                )
                    except Exception:
                        pass

    def list_plugins(self) -> list[PluginInfo]:
        descriptors = self._registry.list_plugins()
        result: list[PluginInfo] = []
        for d in descriptors:
            m = d.metadata
            result.append(
                PluginInfo(
                    name=m.name or m.id,
                    version=m.version or "0.0.0",
                    type=m.plugin_type.value,
                    enabled=d.status.value == "registered",
                    compatible=True,
                )
            )
        return result

    def get_version_info(self) -> VersionInfo:
        import sys

        from specmetrics import __version__ as platform_version

        return VersionInfo(
            platform_version=platform_version,
            python_version=sys.version.split()[0],
            plugins=self.list_plugins(),
        )

    def execute(self, request: PipelineRequest) -> PipelineResult:
        started_at = datetime.now(timezone.utc)

        if not request.project_path.exists():
            return PipelineResult(
                status=PipelineStatus.FAILED,
                error=f"Project path not found: {request.project_path}",
            )

        self.discover_plugins(metrics_filter=request.metrics_filter)

        event_order = _resolve_event_order(request.stages, request.from_stage)

        engine = PipelineEngine(self._handler_registry)
        adapter_registry = AdapterRegistry(self._registry)

        config_provider = None
        if self._config_system is not None:
            try:
                config_provider = self._config_system.load()
            except Exception:
                logger.warning("config_load_failed")

        llm_gateway = LLMGateway(LLMGatewayConfig(rpm_limit=request.llm_rpm_limit))

        context = PipelineContext(
            repository=request.project_path,
            metadata={
                "adapter_registry": adapter_registry,
                "config": config_provider,
                "llm_gateway": llm_gateway,
            },
        )

        try:
            result_ctx = engine.run(context)
        except PipelineError as exc:
            elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
            return PipelineResult(
                status=PipelineStatus.FAILED,
                project_path=request.project_path,
                error=str(exc),
                duration_seconds=elapsed,
            )

        elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()

        stages_executed = self._build_stage_results(
            result_ctx, event_order, request.metrics_filter
        )
        measurement = self._extract_measurement(result_ctx)
        metric_results = self._build_metric_results(result_ctx, request.metrics_filter)
        output_errors = self._build_output_errors(result_ctx)
        llm_provider, llm_model = self._get_llm_info()
        export_path = self._handle_export(request, result_ctx)
        stage_entities = self._build_stage_entities(
            result_ctx, event_order, export_path
        )
        stage_details = self._build_stage_details(
            result_ctx, event_order, request.metrics_filter, export_path
        )

        max_entities_per_stage = 5000
        if config_provider is not None:
            try:
                max_entities_per_stage = config_provider.get(
                    "run_artifacts.max_entities_per_stage", 5000
                )
            except Exception:
                pass

        has_failures = any(
            s.status == StageExecutionStatus.FAILED for s in stages_executed
        )

        measurement_result_raw: dict[str, Any] = {}
        mr = getattr(result_ctx, "measurement_result", None)
        if isinstance(mr, dict):
            measurement_result_raw = mr

        llm_call_stats = llm_gateway.get_summary_stats()

        return PipelineResult(
            status=PipelineStatus.FAILED if has_failures else PipelineStatus.SUCCESS,
            project_path=request.project_path,
            run_id=str(result_ctx.execution_id),
            stages_executed=stages_executed,
            measurement=measurement,
            duration_seconds=elapsed,
            export_path=export_path,
            _framework_detected=getattr(self, "_framework_detected", ""),
            canonical_model=result_ctx.canonical_model,
            metric_results=metric_results,
            stage_entities=stage_entities,
            stage_details=stage_details,
            output_errors=output_errors,
            llm_provider=llm_provider,
            llm_model=llm_model,
            _max_entities_per_stage=max_entities_per_stage,
            measurement_result_raw=measurement_result_raw,
            llm_call_stats=llm_call_stats,
        )

    def _build_stage_entities(
        self,
        ctx: PipelineContext,
        event_order: list[EventType],
        export_path: Path | None,
    ) -> dict[str, list[dict]]:
        entities: dict[str, list[dict]] = {}
        valid_stage_names = {s.value for s in StageName}

        for event_type in event_order:
            stage_name = _stage_name_from_event(event_type)
            if stage_name not in valid_stage_names:
                continue

            stage_entities: list[dict] = []

            if stage_name == "discover":
                adapter_data = getattr(ctx, "adapter_result", None) or {}
                for doc in adapter_data.get("documents", []):
                    stage_entities.append(
                        {
                            "id": str(getattr(doc, "id", "")),
                            "document_type": str(getattr(doc, "document_type", "")),
                            "path": str(getattr(doc, "path", "")),
                        }
                    )

            elif stage_name == "extract":
                extract_data = getattr(ctx, "extraction_result", None) or {}
                results_dict = extract_data.get("results", {})
                for provider_id, provider_result in results_dict.items():
                    for elem in provider_result.get("elements", []):
                        elem_id = (
                            str(elem.get("id", ""))
                            if isinstance(elem, dict)
                            else str(getattr(elem, "id", ""))
                        )
                        elem_type = (
                            str(elem.get("type", ""))
                            if isinstance(elem, dict)
                            else str(getattr(elem, "type", ""))
                        )
                        elem_content = (
                            elem.get("content")
                            if isinstance(elem, dict)
                            else getattr(elem, "content", None)
                        )
                        if not elem_id and not elem_type and not elem_content:
                            continue
                        evidence = (
                            elem.get("evidence")
                            if isinstance(elem, dict)
                            else getattr(elem, "evidence", None)
                        )
                        stage_entities.append(
                            {
                                "id": elem_id,
                                "type": elem_type,
                                "content": _truncate_text(elem_content),
                                "confidence": float(
                                    elem.get("confidence", 0.0)
                                    if isinstance(elem, dict)
                                    else getattr(elem, "confidence", 0.0)
                                ),
                                "evidence": {
                                    "document_id": str(evidence.get("document_id", ""))
                                    if isinstance(evidence, dict)
                                    else str(getattr(evidence, "document_id", "")),
                                    "section_id": str(evidence.get("section_id", None))
                                    if isinstance(evidence, dict)
                                    else str(getattr(evidence, "section_id", None)),
                                    "text": _truncate_text(
                                        evidence.get("text")
                                        if isinstance(evidence, dict)
                                        else getattr(evidence, "text", None)
                                    ),
                                }
                                if evidence
                                else {},
                            }
                        )
                docs_proc = extract_data.get("documents_processed", 0)
                docs_skip = extract_data.get("documents_skipped", 0)
                stage_entities.append(
                    {
                        "type": "documents_processed",
                        "count": docs_proc,
                    }
                )
                stage_entities.append(
                    {
                        "type": "documents_skipped",
                        "count": docs_skip,
                    }
                )

            elif stage_name == "graph":
                graph_data = getattr(ctx, "evidence_graph", None) or {}
                if isinstance(graph_data, dict):
                    for node in graph_data.get("nodes", []):
                        if isinstance(node, dict):
                            stage_entities.append(
                                {
                                    "id": node.get("id", ""),
                                    "node_type": node.get("node_type", ""),
                                    "semantic_type": node.get("semantic_type"),
                                    "document_id": node.get("document_id"),
                                    "section_id": node.get("section_id"),
                                    "text": _truncate_text(node.get("text")),
                                }
                            )
                    stage_entities.append(
                        {
                            "node_type": "graph_summary",
                            "edge_count": graph_data.get("edge_count", 0),
                            "run_id": graph_data.get("run_id", ""),
                        }
                    )

            elif stage_name == "csm":
                csm = getattr(ctx, "canonical_spec_model", None)
                if isinstance(csm, CanonicalSpecificationModel):
                    category_map = {
                        "specification_activity": csm.specification_activities,
                        "decision": csm.decisions,
                        "assumption": csm.assumptions,
                        "constraint": csm.constraints,
                        "risk": csm.risks,
                        "open_question": csm.open_questions,
                        "acceptance_criterion": csm.acceptance_criteria,
                        "glossary_term": csm.glossary_terms,
                        "reference": csm.references,
                    }
                    for cat_name, cat_dict in category_map.items():
                        for element in cat_dict.values():
                            dumped = element.model_dump(mode="json")
                            dumped["type"] = cat_name
                            if "description" in dumped:
                                dumped["description"] = _truncate_text(
                                    dumped["description"]
                                )
                            stage_entities.append(dumped)

            elif stage_name == "cfm":
                cfm = getattr(ctx, "canonical_model", None)
                if isinstance(cfm, CanonicalFunctionalModel):
                    category_map = {
                        "actor": cfm.actors,
                        "functional_process": cfm.functional_processes,
                        "business_rule": cfm.business_rules,
                        "data_group": cfm.data_groups,
                        "operation": cfm.operations,
                        "unclassified": cfm.unclassified,
                    }
                    for cat_name, cat_dict in category_map.items():
                        for element in cat_dict.values():
                            dumped = element.model_dump(mode="json")
                            dumped["type"] = cat_name
                            stage_entities.append(dumped)
                    for rel in cfm.relationships:
                        dumped = rel.model_dump(mode="json")
                        dumped["type"] = "relationship"
                        stage_entities.append(dumped)

            elif stage_name == "rule":
                cfm = getattr(ctx, "canonical_model", None)
                if isinstance(cfm, CanonicalFunctionalModel):
                    for rule_pack in getattr(cfm.metadata, "applied_rules", []):
                        if isinstance(rule_pack, dict):
                            stage_entities.append(
                                {
                                    "type": "applied_rule_pack",
                                    "rule_pack_id": rule_pack.get("rule_pack_id", ""),
                                    "rule_id": rule_pack.get("rule_id", ""),
                                    "rule_type": rule_pack.get("rule_type", ""),
                                    "methodology": rule_pack.get("methodology", ""),
                                    "description": rule_pack.get("description", ""),
                                }
                            )
                    stage_entities.append(
                        {
                            "type": "modification_summary",
                            "entities_modified": sum(
                                cfm.metadata.element_counts.values()
                            )
                            if hasattr(cfm.metadata, "element_counts")
                            else 0,
                            "vaf_applied": getattr(cfm.metadata, "vaf", None),
                        }
                    )

            elif stage_name == "measure":
                mr = getattr(ctx, "measurement_result", None) or {}
                if isinstance(mr, dict):
                    metric_ids = list(METRIC_NAME_MAP.values())
                    key_map = {
                        "function_points": (
                            "fpa_total_function_points",
                            "fpa_breakdown",
                        ),
                        "simplified_function_points": ("sfp_total_sfp", None),
                        "business_complexity_points": ("bcp_measured_items", None),
                        "token_points": ("token_total_score", None),
                        "cognitive_points": ("cognitive_raw_score", "cognitive_bloom_breakdown"),
                        "story_points": ("storypoints_total_story_points", None),
                        "snap": ("snap_total_snap", None),
                        "tshirt": ("tshirt", "tshirt_breakdown"),
                    }
                    metric_name_to_cli = {v: k for k, v in METRIC_NAME_MAP.items()}
                    for metric_name in metric_ids:
                        total_key, breakdown_key = key_map.get(
                            metric_name, (None, None)
                        )
                        total = mr.get(total_key, 0) if total_key else 0
                        if metric_name in ("token_points", "cognitive_points"):
                            total = round(total, 1)
                        entry: dict = {
                            "metric": metric_name,
                            "total": total,
                            "status": "completed",
                            "duration_ms": 0,
                        }
                        if breakdown_key and breakdown_key in mr:
                            bd = mr[breakdown_key]
                            if metric_name == "cognitive_points" and isinstance(bd, dict):
                                bd = {
                                    k: {"total": round(v["total"], 1)} if isinstance(v, dict) else round(v, 1)
                                    for k, v in bd.items()
                                }
                            entry["breakdown"] = bd
                        cli_id = metric_name_to_cli.get(metric_name)
                        if cli_id:
                            warning_key = f"{cli_id}_warnings"
                            raw_warnings = mr.get(warning_key, [])
                            if isinstance(raw_warnings, list) and raw_warnings:
                                entry["warnings"] = [
                                    w.get("message", str(w)) if isinstance(w, dict) else str(w)
                                    for w in raw_warnings
                                ]
                        stage_entities.append(entry)

            elif stage_name == "export":
                if export_path:
                    try:
                        rel = export_path.relative_to(ctx.repository)
                    except (ValueError, AttributeError):
                        rel = export_path
                    stage_entities.append(
                        {
                            "format": "json",
                            "path": str(rel),
                        }
                    )

            entities[stage_name] = stage_entities

        return entities

    def _build_stage_results(
        self,
        ctx: PipelineContext,
        event_order: list[EventType],
        metrics_filter: list[str] | None = None,
    ) -> list[StageResult]:
        if not ctx.diagnostics:
            return []

        results: list[StageResult] = []
        valid_stage_names = {s.value for s in StageName}

        for event_type in event_order:
            stage_name = _stage_name_from_event(event_type)
            if stage_name not in valid_stage_names:
                continue

            timing = ctx.diagnostics.stage_timings.get(stage_name)
            if timing is None:
                alt_names = _STAGE_NAME_TO_HANDLER_NAMES.get(stage_name, [])
                for alt_name in alt_names:
                    timing = ctx.diagnostics.stage_timings.get(alt_name)
                    if timing is not None:
                        break

            if timing is None:
                results.append(
                    StageResult(
                        stage=StageName(stage_name),
                        status=StageExecutionStatus.SKIPPED,
                    )
                )
                continue

            kernel_status = timing.status
            if kernel_status == KernelStageStatus.COMPLETED:
                status = StageExecutionStatus.COMPLETED
            elif kernel_status == KernelStageStatus.FAILED:
                status = StageExecutionStatus.FAILED
            elif kernel_status == KernelStageStatus.RUNNING:
                status = StageExecutionStatus.RUNNING
            else:
                status = StageExecutionStatus.PENDING

            duration_s = (
                (timing.duration_ms or 0) / 1000.0
                if timing.duration_ms is not None
                else 0.0
            )

            entities_found = 0
            if stage_name == "discover":
                adapter_data = getattr(ctx, "adapter_result", None) or {}
                entities_found = len(adapter_data.get("documents", []))
                adapters = adapter_data.get("adapters_used", [])
                if "speckit-adapter" in adapters:
                    self._framework_detected = "speckit"
                elif "openspec-adapter" in adapters:
                    self._framework_detected = "openspec"
            elif stage_name == "extract":
                extract_data = getattr(ctx, "extraction_result", None) or {}
                entities_found = extract_data.get("total_elements", 0)
            elif stage_name == "graph":
                graph_data = getattr(ctx, "evidence_graph", None) or {}
                if isinstance(graph_data, dict):
                    entities_found = graph_data.get("node_count", 0)
            elif stage_name == "csm":
                csm = getattr(ctx, "canonical_spec_model", None)
                if isinstance(csm, CanonicalSpecificationModel):
                    entities_found = sum(csm.metadata.element_counts.values())
            elif stage_name == "cfm":
                cfm = getattr(ctx, "canonical_model", None)
                if isinstance(cfm, CanonicalFunctionalModel):
                    entities_found = sum(cfm.metadata.element_counts.values())
            elif stage_name == "rule":
                cfm = getattr(ctx, "canonical_model", None)
                if isinstance(cfm, CanonicalFunctionalModel):
                    entities_found = sum(cfm.metadata.element_counts.values())
            elif stage_name == "measure":
                entities_found = (
                    len(metrics_filter) if metrics_filter else len(METRIC_NAME_MAP)
                )

            results.append(
                StageResult(
                    stage=StageName(stage_name),
                    status=status,
                    duration_seconds=duration_s,
                    entities_found=entities_found,
                )
            )
        return results

    def _extract_measurement(self, ctx: PipelineContext) -> MeasurementResult | None:
        if ctx.measurement_result is None:
            return None

        mr = ctx.measurement_result
        if isinstance(mr, dict):
            return MeasurementResult(
                total_function_points=mr.get("fpa_total_function_points", 0),
                breakdown=mr.get("fpa_breakdown", {}),
                complexity_distribution=mr.get("fpa_complexity_distribution", []),
                evidence_refs=mr.get("evidence_refs", []),
                applied_rule_pack=mr.get("storypoints_applied_rule_pack", ""),
            )
        return MeasurementResult()

    def _build_metric_results(
        self,
        ctx: PipelineContext,
        metrics_filter: list[str] | None,
    ) -> list[MetricOutputItem]:
        mr = ctx.measurement_result
        if not isinstance(mr, dict):
            return []

        metric_ids = metrics_filter or list(METRIC_NAME_MAP.keys())
        results: list[MetricOutputItem] = []

        for mid in metric_ids:
            json_name = METRIC_NAME_MAP.get(mid, mid)
            key_map = {
                "bcp": "bcp_measured_items",
                "fpa": "fpa_total_function_points",
                "sfp": "sfp_total_sfp",
                "snap": "snap_total_snap",
                "sp": "storypoints_total_story_points",
                "tshirt": "tshirt",
                "tp": "token_total_score",
                "cp": "cognitive_raw_score",
            }
            total_key = key_map.get(mid)
            total = mr.get(total_key, 0) if total_key else 0

            results.append(
                MetricOutputItem(
                    name=json_name,
                    total=total,
                    status="completed",
                    duration_ms=0,
                )
            )

        return results

    def _build_stage_details(
        self,
        ctx: PipelineContext,
        event_order: list[EventType],
        metrics_filter: list[str] | None = None,
        export_path: Path | None = None,
    ) -> list[StageOutputItem]:
        if not ctx.diagnostics:
            return []

        details: list[StageOutputItem] = []
        valid_stage_names = {s.value for s in StageName}

        for event_type in event_order:
            stage_name = _stage_name_from_event(event_type)
            if stage_name not in valid_stage_names:
                continue

            timing = ctx.diagnostics.stage_timings.get(stage_name)
            if timing is None:
                alt_names = _STAGE_NAME_TO_HANDLER_NAMES.get(stage_name, [])
                for alt_name in alt_names:
                    timing = ctx.diagnostics.stage_timings.get(alt_name)
                    if timing is not None:
                        break

            duration_ms = (
                timing.duration_ms if timing and timing.duration_ms is not None else 0
            )

            count = 0
            count_type = "items"
            if stage_name == "discover":
                adapter_data = getattr(ctx, "adapter_result", None) or {}
                count = len(adapter_data.get("documents", []))
                count_type = "documents"
            elif stage_name == "extract":
                extract_data = getattr(ctx, "extraction_result", None) or {}
                count = extract_data.get("total_elements", 0)
            elif stage_name == "graph":
                graph_data = getattr(ctx, "evidence_graph", None) or {}
                if isinstance(graph_data, dict):
                    count = graph_data.get("node_count", 0)
            elif stage_name == "csm":
                csm = getattr(ctx, "canonical_spec_model", None)
                if isinstance(csm, CanonicalSpecificationModel):
                    count = sum(csm.metadata.element_counts.values())
            elif stage_name == "cfm":
                cfm = getattr(ctx, "canonical_model", None)
                if isinstance(cfm, CanonicalFunctionalModel):
                    count = sum(cfm.metadata.element_counts.values())
            elif stage_name == "rule":
                cfm = getattr(ctx, "canonical_model", None)
                if isinstance(cfm, CanonicalFunctionalModel):
                    count = sum(cfm.metadata.element_counts.values())
            elif stage_name == "measure":
                mr = getattr(ctx, "measurement_result", None) or {}
                if isinstance(mr, dict):
                    count = (
                        len(metrics_filter) if metrics_filter else len(METRIC_NAME_MAP)
                    )
                count_type = "metrics"
            elif stage_name == "export":
                count = 1 if export_path else 0
                count_type = "files"

            details.append(
                StageOutputItem(
                    name=stage_name,
                    count=count,
                    count_type=count_type,
                    duration_ms=duration_ms,
                )
            )

        return details

    def _build_output_errors(self, ctx: PipelineContext) -> list[ErrorOutputItem]:
        if not ctx.diagnostics or not ctx.diagnostics.errors:
            return []
        return [
            ErrorOutputItem(
                stage=str(getattr(err, "stage_name", "")),
                message=getattr(err, "message", str(err)),
            )
            for err in ctx.diagnostics.errors
        ]

    def _get_llm_info(self) -> tuple[str, str]:
        provider = "none"
        model = ""
        if self._config_system is not None:
            try:
                cfg = self._config_system.load()
                if cfg:
                    provider = getattr(cfg, "llm_provider", "") or "none"
                    model = getattr(cfg, "llm_model", "") or ""
            except Exception:
                pass
        return provider, model

    def _write_json_output(
        self,
        request: PipelineRequest,
        ctx: PipelineContext,
        export_dir: Path,
        metric_results: list[MetricOutputItem],
        stage_details: list[StageOutputItem],
        output_errors: list[ErrorOutputItem],
    ) -> Path:
        export_file = export_dir / "specmetrics-output.json"

        llm_provider, llm_model = self._get_llm_info()

        llm_info: dict[str, str] = {"provider": llm_provider}
        if llm_model:
            llm_info["model"] = llm_model

        measure_meta = MeasureMetadata(
            id=request.measure_id,
            id_path=request.measure_id,
            sdd_framework=getattr(self, "_framework_detected", "") or "unknown",
            created=datetime.now(timezone.utc).isoformat(),
            llm=llm_info,
            project_path=str(request.project_path),
        )

        output = MeasureOutput(
            measure=measure_meta,
            results=[
                OutputMetricResult(
                    name=r.name,
                    total=r.total,
                    status=r.status,
                    duration_ms=r.duration_ms,
                )
                for r in metric_results
            ],
            stages=[
                OutputStageInfo(
                    name=s.name,
                    count=s.count,
                    count_type=s.count_type,
                    duration_ms=s.duration_ms,
                )
                for s in stage_details
            ],
            errors=[
                ErrorRecord(
                    stage=e.stage,
                    message=e.message,
                    details=e.details,
                )
                for e in output_errors
            ],
        )

        export_file.write_text(output.model_dump_json(indent=2))
        logger.info("json_export_written", path=str(export_file))
        return export_file

    def _handle_export(
        self, request: PipelineRequest, ctx: PipelineContext
    ) -> Path | None:
        if request.output_format == OutputFormat.NONE:
            return None

        export_dir = (
            request.output_path
            if request.output_path
            else request.project_path / ".specmetrics" / "output"
        )
        export_dir.mkdir(parents=True, exist_ok=True)

        if request.output_format in (
            OutputFormat.JSON,
            OutputFormat.CSV,
            OutputFormat.XML,
        ):
            return self._handle_structured_export(request, ctx, export_dir)

        export_file = export_dir / "specmetrics-output.json"

        metric_results = self._build_metric_results(ctx, request.metrics_filter)
        stage_details = self._build_stage_details(
            ctx, list(CANONICAL_EVENT_ORDER), request.metrics_filter, export_file
        )
        output_errors = self._build_output_errors(ctx)

        self._write_json_output(
            request, ctx, export_dir, metric_results, stage_details, output_errors
        )
        logger.info("export_written", path=str(export_file))
        return export_file

    def _handle_structured_export(
        self, request: PipelineRequest, ctx: PipelineContext, export_dir: Path
    ) -> Path | None:
        from importlib.metadata import entry_points

        from specmetrics.plugins.exporter.base import ExporterPlugin
        from specmetrics.plugins.exporter.orchestrator import ExportOrchestrator

        exporters: list[ExporterPlugin] = []
        for ep in entry_points(group="specmetrics.exporters"):
            try:
                cls = ep.load()
                if isinstance(cls, type) and issubclass(cls, ExporterPlugin):
                    exporters.append(cls())
            except Exception as exc:
                logger.warning(
                    "exporter_load_failed", entry_point=ep.name, error=str(exc)
                )

        if not exporters:
            logger.warning("No exporter plugins available for structured export")
            return None

        cfm = ctx.canonical_model
        if cfm is None:
            logger.warning("No canonical model available for export")
            return None

        orch = ExportOrchestrator(exporters)
        fmt = request.output_format.value
        orch.export_to_dir(cfm, export_dir, formats=[fmt])
        export_file = export_dir / f"measurements.{fmt}"
        logger.info("structured_export_completed", format=fmt, path=str(export_file))
        return export_file
