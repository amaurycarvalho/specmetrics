"""Shared BCP measurement loop and work item construction."""
from __future__ import annotations

from collections.abc import Callable

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel

from .models import BCPWorkItem, MeasurementEvidence, SDKResult
from .story_generator import generate_story


def make_failed_item(
    fp_id: str,
    fp: object,
    story: str,
    sdk_result: SDKResult,
    include_evidence: bool,
) -> BCPWorkItem:
    """Build a failed BCP work item for a functional process."""
    kwargs: dict = {
        "element_id": fp_id,
        "element_name": fp.name,
        "generated_story": story,
        "sdk_response": sdk_result.raw_response,
        "bcp_score": 0.0,
        "status": "failed",
    }
    if include_evidence:
        kwargs["evidence_refs"] = [
            MeasurementEvidence(
                element_id=fp_id,
                document_id=getattr(fp.evidence, "document_id", ""),
                text=getattr(fp.evidence, "text", ""),
            )
        ]
    return BCPWorkItem(**kwargs)


def make_success_item(
    fp_id: str,
    fp: object,
    story: str,
    sdk_result: SDKResult,
    include_evidence: bool,
) -> BCPWorkItem:
    """Build a successful BCP work item for a functional process."""
    kwargs: dict = {
        "element_id": fp_id,
        "element_name": fp.name,
        "generated_story": story,
        "sdk_response": sdk_result.raw_response,
        "bcp_score": sdk_result.total_bcp,
        "component_breakdown": sdk_result.breakdown,
        "status": "success",
    }
    if include_evidence:
        kwargs["evidence_refs"] = [
            MeasurementEvidence(
                element_id=fp_id,
                document_id=getattr(fp.evidence, "document_id", ""),
                text=getattr(fp.evidence, "text", ""),
            )
        ]
    return BCPWorkItem(**kwargs)


def measure_all(
    cfm: CanonicalFunctionalModel,
    adapter: object,
    *,
    record_request: Callable[[], None] | None = None,
    record_success: Callable[[float], None] | None = None,
    record_error: Callable[[int], None] | None = None,
    include_evidence: bool,
) -> tuple[list[BCPWorkItem], int, int, int, int]:
    """Measure BCP for every functional process in the CFM."""
    items: list[BCPWorkItem] = []
    succeeded = 0
    failed = 0
    sdk_call_count = 0
    sdk_errors = 0

    for fp_id, fp in cfm.functional_processes.items():
        story = generate_story(fp, cfm)

        if record_request is not None:
            record_request()

        sdk_result = adapter.calculate(story)
        sdk_call_count += 1

        if sdk_result.errors:
            failed += 1
            sdk_errors += len(sdk_result.errors)
            if record_error is not None:
                record_error(len(sdk_result.errors))
            items.append(make_failed_item(fp_id, fp, story, sdk_result, include_evidence))
        else:
            succeeded += 1
            if record_success is not None:
                record_success(sdk_result.duration_ms)
            items.append(make_success_item(fp_id, fp, story, sdk_result, include_evidence))

    return items, succeeded, failed, sdk_call_count, sdk_errors