"""Shared state dataclasses for the semantic extraction visitors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Observation:
    """A single structured observation extracted from a document."""

    type: str
    content: str
    context: dict[str, Any] = field(default_factory=dict)
    location: tuple[str, str | None] = ("", None)


@dataclass
class ExtractionState:
    """Mutable state shared between visitors during extraction."""

    heading_stack: list[str] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)
    elements: list = field(default_factory=list)