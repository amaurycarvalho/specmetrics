"""Extraction helpers used by the T-Shirt handler."""
from __future__ import annotations

from typing import Self

from specmetrics.kernel.pipeline_context import PipelineContext


class _ItemExtractionMixin:
    """Extracts story point values and metadata from arbitrary results."""

    def _extract_sp_items(self: Self, measurement_result: object) -> list | None:
        if measurement_result is None:
            return None
        if isinstance(measurement_result, dict):
            return (
                measurement_result.get("storypoints_entities")
                or measurement_result.get("items")
                or measurement_result.get("estimated_items")
            )
        if hasattr(measurement_result, "items"):
            return measurement_result.items
        return None

    def _extract_run_id(self: Self, measurement_result: object) -> str | None:
        if measurement_result is None:
            return None
        if isinstance(measurement_result, dict):
            return (
                measurement_result.get("run_id")
                or measurement_result.get("storypoints_run_id")
                or measurement_result.get("execution_id")
            )
        if hasattr(measurement_result, "run_id"):
            return measurement_result.run_id
        return None

    def _get_sp_value(self: Self, item: object) -> int | None:
        if isinstance(item, dict):
            val = (
                item.get("normalized_value")
                or item.get("story_point_value")
                or item.get("value")
            )
            return int(val) if val is not None else None
        for attr in ("normalized_value", "story_point_value", "value"):
            val = getattr(item, attr, None)
            if val is not None:
                return int(val)
        return None

    def _get_elem_id(self: Self, item: object) -> str:
        if isinstance(item, dict):
            return str(item.get("element_id", ""))
        return str(getattr(item, "element_id", ""))

    def _get_elem_name(self: Self, item: object) -> str:
        if isinstance(item, dict):
            return str(item.get("element_name", ""))
        return str(getattr(item, "element_name", ""))

    def _resolve_mapping_override(self: Self, ctx: PipelineContext) -> list | None:
        metadata = ctx.metadata
        if metadata is None:
            return None
        extra = (
            metadata
            if isinstance(metadata, dict)
            else getattr(metadata, "extra", None) or {}
        )
        raw = extra.get("tshirt_mapping") if isinstance(extra, dict) else None
        if raw is None:
            return None
        from .models import TShirtSize

        sizes: list[TShirtSize] = []
        for entry in raw:
            sizes.append(
                TShirtSize(
                    label=entry["label"],
                    story_point_range=tuple(entry["story_point_range"]),
                    ordinal=entry.get("ordinal", len(sizes) + 1),
                )
            )
        return sizes