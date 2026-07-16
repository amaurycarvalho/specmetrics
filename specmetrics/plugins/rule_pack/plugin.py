from __future__ import annotations


from typing import Callable

import structlog

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.cfm.models import RulePack, RuleValidationReport, ValidationError
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType

from .annotator import RuleAnnotator
from .applicator import RuleApplicator
from .loader import RulePackLoader
from .validator import RulePackValidator

logger = structlog.get_logger(__name__)

RULES_DIR = ".specify/rules"


class RulePackEnginePlugin:
    def __init__(
        self,
        rules_dir: str = RULES_DIR,
    ) -> None:
        self._loader = RulePackLoader(rules_dir)
        self._validator = RulePackValidator()
        self._applicator = RuleApplicator()
        self._annotator = RuleAnnotator()
        self._rules_dir = rules_dir

    @property
    def handled_event_type(self) -> EventType:
        return EventType.RULE_PACK_APPLIED

    @property
    def handler_id(self) -> str:
        return "rule_pack_engine"

    @property
    def stage_name(self) -> str:
        return "Rule Pack Engine"

    def handle(self, event: PipelineEvent) -> PipelineContext:
        ctx = event.context
        cfm: CanonicalFunctionalModel | None = ctx.canonical_model

        if cfm is None:
            logger.warning("rule_pack_engine_no_cfm", execution_id=str(ctx.execution_id))
            return ctx

        logger.info(
            "rule_pack_engine_started",
            execution_id=str(ctx.execution_id),
            rules_dir=self._rules_dir,
        )

        packs, report = self._load_and_validate()

        for err in report.errors:
            logger.error(
                "rule_pack_validation_error",
                file=err.file_path,
                message=err.message,
                rule_id=err.rule_id,
            )

        for warn in report.warnings:
            logger.warning(
                "rule_pack_validation_warning",
                file=warn.file_path,
                message=warn.message,
                rule_id=warn.rule_id,
            )

        if not packs:
            logger.info("rule_pack_engine_no_rules", execution_id=str(ctx.execution_id))
            self._annotator.clear()
            self._annotator.record_default_rules()
            annotated_cfm = self._annotator.annotate_cfm(cfm)
            return ctx.with_stage_output("canonical_model", annotated_cfm)

        logger.info(
            "rule_pack_engine_loaded",
            pack_count=len(packs),
            total_rules=report.total_rules,
            active_rules=report.active_rules,
        )

        annotated_cfm = self._applicator.apply(cfm, packs)

        return ctx.with_stage_output("canonical_model", annotated_cfm)

    def _load_and_validate(self) -> tuple[list[RulePack], RuleValidationReport]:
        merged_report = RuleValidationReport()
        valid_packs: list[RulePack] = []

        load_results = self._loader.load_all()

        if not load_results:
            return [], merged_report

        for pack, load_result in load_results:
            if pack is None:
                merged_report.errors.append(
                    ValidationError(
                        file_path=load_result.file_path,
                        message=load_result.error,
                    )
                )
                continue
            report = self._validator.validate_pack(pack, load_result)
            merged_report.loaded_files.extend(report.loaded_files)
            merged_report.total_rules += report.total_rules
            merged_report.active_rules += report.active_rules
            merged_report.errors.extend(report.errors)
            merged_report.warnings.extend(report.warnings)
            if not report.errors:
                valid_packs.append(pack)

        return valid_packs, merged_report

    def apply_rules(
        self,
        cfm: CanonicalFunctionalModel,
        packs: list[RulePack] | None = None,
    ) -> CanonicalFunctionalModel:
        if packs is None:
            packs, _ = self._load_and_validate()
        if not packs:
            return cfm
        return self._applicator.apply(cfm, packs)


def create_rule_pack_engine_metadata() -> PluginMetadata:
    return PluginMetadata(
        id="rule_pack_engine",
        api_version="0.1.0",
        plugin_type=PluginType.MEASUREMENT,
        handled_event_types=(EventType.RULE_PACK_APPLIED,),
        handler_factory=lambda: RulePackEnginePlugin(),
        name="Rule Pack Engine",
        description="Loads, validates, and applies Rule Pack rules to the Canonical Functional Model",
        version="0.1.0",
    )
