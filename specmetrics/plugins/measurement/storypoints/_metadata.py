"""Execution metadata model for Story Points measurement."""
from __future__ import annotations

from typing import Self

from pydantic import BaseModel, model_validator


class ExecutionMetadata(BaseModel):
    """Execution metadata for a Story Points measurement run."""

    duration_ms: float = 0.0
    total_elements_processed: int = 0
    cfm_elements_processed: int = 0
    csm_elements_processed: int = 0
    total_fps_processed: int = 0
    fps_estimated: int = 0
    fps_merged_as_duplicates: int = 0
    elements_without_base_weight: int = 0
    version: str = "1.0"

    @model_validator(mode="after")
    def validate_counts(self: Self) -> ExecutionMetadata:
        """Validate that element and process counts are consistent."""
        if (
            self.total_fps_processed
            != self.fps_estimated + self.fps_merged_as_duplicates
        ):
            raise ValueError(
                f"total_fps_processed ({self.total_fps_processed}) must equal "
                f"fps_estimated ({self.fps_estimated}) + "
                f"fps_merged_as_duplicates ({self.fps_merged_as_duplicates})"
            )
        if (
            self.cfm_elements_processed + self.csm_elements_processed
            != self.total_elements_processed
        ) and self.total_elements_processed != 0:
            raise ValueError(
                f"total_elements_processed ({self.total_elements_processed}) "
                f"must equal cfm_elements_processed + csm_elements_processed "
                f"({self.cfm_elements_processed} + {self.csm_elements_processed})"
            )
        if self.total_elements_processed > 0:
            expected_total = self.cfm_elements_processed + self.csm_elements_processed
            if self.total_elements_processed != expected_total:
                raise ValueError(
                    f"total_elements_processed ({self.total_elements_processed}) "
                    f"must equal cfm_elements_processed + csm_elements_processed "
                    f"({expected_total})"
                )
        return self