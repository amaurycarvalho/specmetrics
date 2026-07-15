from __future__ import annotations

from typing import Literal, Optional

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
    function_types: Optional[list[str]] = None
    function_type: Optional[str] = None
    complexity: Optional[str] = None
    weight: Optional[int] = None
    thresholds: Optional[dict[str, list[int]]] = None
    element_ids: Optional[list[str]] = None
    gsc: Optional[dict[str, int]] = None


class Rule(BaseModel):
    id: str
    type: RuleTypeName
    description: str = ""
    config: RuleConfig


class RulePack(BaseModel):
    id: str
    description: str = ""
    methodology: str = "APF"
    rules: list[Rule] = []
    glossary_overrides: dict[str, str] = {}


class AppliedRuleRecord(BaseModel):
    rule_pack_id: str
    rule_id: str
    rule_type: str
    description: str = ""
    before_state: dict[str, object] = {}
    after_state: dict[str, object] = {}


class FileLoadResult(BaseModel):
    file_path: str
    rule_pack_id: str = ""
    status: str = "loaded"
    rules_count: int = 0
    error: str = ""


class ValidationError(BaseModel):
    file_path: str
    message: str
    rule_id: Optional[str] = None
    field: Optional[str] = None


class ValidationWarning(BaseModel):
    file_path: str
    message: str
    rule_id: Optional[str] = None


class RuleValidationReport(BaseModel):
    loaded_files: list[FileLoadResult] = []
    total_rules: int = 0
    active_rules: int = 0
    errors: list[ValidationError] = []
    warnings: list[ValidationWarning] = []
