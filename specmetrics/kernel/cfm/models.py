"""Supporting data models for CFM rule packs and validation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

FunctionType = Literal["ILF", "EIF", "EI", "EO", "EQ"]
ComplexityRating = Literal["Low", "Average", "High"]
RuleTypeName = Literal[
    "exclusion",
    "complexity_override",
    "weight_override",
    "vaf",
    "element_exclusion",
]


class RuleConfig(BaseModel):
    """Configuration for a rule pack rule."""

    function_types: list[str] | None = None
    function_type: str | None = None
    complexity: str | None = None
    weight: int | None = None
    thresholds: dict[str, list[int]] | None = None
    element_ids: list[str] | None = None
    gsc: dict[str, int] | None = None


class Rule(BaseModel):
    """A single rule within a rule pack."""

    id: str
    type: RuleTypeName
    description: str = ""
    config: RuleConfig


class RulePack(BaseModel):
    """A set of rules applied during measurement."""

    id: str
    description: str = ""
    methodology: str = "FPA"
    rules: list[Rule] = []
    glossary_overrides: dict[str, str] = {}


class AppliedRuleRecord(BaseModel):
    """Record of a rule applied during measurement."""

    rule_pack_id: str
    rule_id: str
    rule_type: str
    description: str = ""
    methodology: str = ""
    before_state: dict[str, object] = {}
    after_state: dict[str, object] = {}


class FileLoadResult(BaseModel):
    """Outcome of loading a rule pack file."""

    file_path: str
    rule_pack_id: str = ""
    status: str = "loaded"
    rules_count: int = 0
    error: str = ""


class ValidationError(BaseModel):
    """An error found while validating a rule pack."""

    file_path: str
    message: str
    rule_id: str | None = None
    field: str | None = None


class ValidationWarning(BaseModel):
    """A warning found while validating a rule pack."""

    file_path: str
    message: str
    rule_id: str | None = None


class RuleValidationReport(BaseModel):
    """Report summarizing rule pack loading and validation."""

    loaded_files: list[FileLoadResult] = []
    total_rules: int = 0
    active_rules: int = 0
    errors: list[ValidationError] = []
    warnings: list[ValidationWarning] = []
