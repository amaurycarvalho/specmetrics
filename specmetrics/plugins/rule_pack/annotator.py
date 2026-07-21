from __future__ import annotations


import structlog

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.cfm.models import AppliedRuleRecord

logger = structlog.get_logger(__name__)


class RuleAnnotator:
    def __init__(self) -> None:
        self._records: list[AppliedRuleRecord] = []

    @property
    def records(self) -> list[AppliedRuleRecord]:
        return self._records

    def clear(self) -> None:
        self._records.clear()

    def record_application(
        self,
        rule_pack_id: str,
        rule_id: str,
        rule_type: str,
        description: str,
        methodology: str = "",
        before_state: dict[str, object] | None = None,
        after_state: dict[str, object] | None = None,
    ) -> AppliedRuleRecord:
        record = AppliedRuleRecord(
            rule_pack_id=rule_pack_id,
            rule_id=rule_id,
            rule_type=rule_type,
            description=description,
            methodology=methodology,
            before_state=before_state or {},
            after_state=after_state or {},
        )
        self._records.append(record)
        return record

    def record_default_rules(self) -> AppliedRuleRecord:
        return self.record_application(
            rule_pack_id="",
            rule_id="",
            rule_type="default",
            description="No Rule Pack files found. Default IFPUG rules applied.",
        )

    def annotate_cfm(
        self,
        cfm: CanonicalFunctionalModel,
        glossary_overrides: dict[str, str] | None = None,
    ) -> CanonicalFunctionalModel:
        metadata_dict = cfm.metadata.model_dump() if cfm.metadata else {}
        applied_dumps = [r.model_dump() for r in self._records]
        metadata_dict["applied_rules"] = applied_dumps

        if glossary_overrides:
            metadata_dict["glossary_overrides"] = glossary_overrides

        from specmetrics.kernel.cfm.metadata import BuildMetadata

        new_metadata = BuildMetadata(**metadata_dict)
        return cfm.model_copy(update={"metadata": new_metadata})
