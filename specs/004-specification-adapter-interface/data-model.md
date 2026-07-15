# Data Model: Specification Adapter Plugin Interface

**Date**: 2026-07-15 | **Spec**: [spec.md](spec.md)

---

## Entity-Relationship Overview

```
SpecificationAdapter (Protocol — implemented per SDD framework)
    │
    ├── scan(repository_path) ──► list[Document]
    ├── supports(path) ──► bool
    │
    └── AdapterRegistry ──► wraps F02 PluginRegistry
                                │
                                └── get_by_type("adapter")
```

---

## Document

Framework-agnostic representation of a specification document. Produced by
adapters and consumed by downstream pipeline stages (F04 Semantic Extraction,
F05 Evidence Graph).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique identifier within the repository |
| `path` | `str` | Yes | Relative path from repository root |
| `document_type` | `str` | Yes | Advisory label (see canonical types below) |
| `content` | `str` | Yes | Raw text content of the document |
| `metadata` | `dict[str, Any]` | No | Framework-specific metadata preserved for traceability |
| `sections` | `list[DocumentSection]` | No | Optional hierarchy breakdown within the document |

**Validation Rules**:
- `id` must be unique within a single `scan()` result
- `path` must be relative (not absolute) and use forward slashes
- `document_type` should use canonical type values when applicable
- `content` may be empty for structural documents (e.g., directories that
  group sub-documents)

---

## DocumentSection

Represents a section or subsection within a document. Enables hierarchy
preservation without full semantic parsing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Section identifier, unique within the document |
| `title` | `str` | Yes | Section heading or title |
| `level` | `int` | Yes | Hierarchy depth (1 = top-level, 2 = subsection, etc.) |
| `content` | `str` | Yes | Raw text content of this section |
| `subsections` | `list[DocumentSection]` | No | Child sections |

---

## SpecificationAdapter (Protocol)

Structural interface that every adapter must implement.

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `scan` | `(repository_path: Path) -> list[Document]` | Document list | Discover all specification documents in the repository |
| `supports` | `(path: Path) -> bool` | `bool` | Return True if this adapter can handle the given repository |

**Behavioral Contracts**:
- `scan()` MUST NOT modify the repository
- `scan()` MUST be idempotent — same path + same state → same result
- `scan()` MUST NOT perform semantic interpretation of content
- `supports()` MUST be fast (no full scan) — typically checks for framework
  markers like `specs/` directory, `specmetrics.yml`, or specific file
  patterns
- Multiple adapters with overlapping `supports()` are allowed; the first
  matching adapter in registration order is used

---

## AdapterRegistry

Convenience wrapper around F02 PluginRegistry for adapter-specific lookups.

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `find_adapter` | `(path: Path) -> SpecificationAdapter \| None` | Adapter or None | Finds the first adapter whose `supports(path)` returns True |
| `list_adapters` | `() -> list[SpecificationAdapter]` | Adapter list | Returns all registered adapter instances |
| `scan_all` | `(path: Path) -> dict[str, list[Document]]` | Adapter → Documents map | Runs `scan()` on all adapters that support the path |

---

## Canonical Document Types

Recommended type labels for `document_type` field. Adapters may use additional
types as needed.

| Type | Typical Content |
|------|-----------------|
| `"use_case"` | UC-01: User Login — description, preconditions, postconditions |
| `"business_rule"` | BR-001: Password must be at least 8 characters |
| `"actor"` | Primary Actor: End User |
| `"process"` | Process: Order Fulfillment — steps, branching |
| `"data_group"` | Data: User Profile — fields, types, constraints |
| `"relationship"` | Relationship: User → Order (one-to-many) |
| `"term"` | Term: "Authentication" — definition |
| `"section"` | General section — heading, body text |
| `"unknown"` | Cannot determine type — raw content preserved |
