"""Pydantic models for calibration profiles."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SpecificationCostWeights(BaseModel):
    """Cost weights for specification elements and activities."""

    activities: dict[str, float] = Field(
        default_factory=lambda: {
            "exploration": 2.0,
            "clarification": 3.0,
            "refinement": 3.0,
            "review": 1.5,
            "validation": 2.0,
        }
    )
    decisions: float = 1.5
    assumptions: float = 1.0
    constraints: float = 1.5
    risks: float = 2.0
    open_questions: float = 1.0
    acceptance_criteria: float = 1.0
    glossary_terms: float = 0.5
    references: float = 1.0


class CodeGenerationCostWeights(BaseModel):
    """Cost weights for code generation elements."""

    functional_processes: float = 5.0
    business_rules: float = 3.0
    operations: float = 2.0
    data_groups: float = 2.0
    relationships: float = 1.0
    actors: float = 1.0


class CalibrationProfile(BaseModel):
    """Calibration profile combining specification and code generation weights."""

    version: str = "1.0"
    specification_cost: SpecificationCostWeights = Field(
        default_factory=SpecificationCostWeights
    )
    code_generation_cost: CodeGenerationCostWeights = Field(
        default_factory=CodeGenerationCostWeights
    )
    content_multiplier: float = 0.1
