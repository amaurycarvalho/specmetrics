# Data Model: Deterministic Semantic Engine

**Date**: 2026-07-17 | **Spec**: [spec.md](spec.md)

---

## Entity-Relationship Overview

```
Pipeline (F01)
    │
    ├── configures provider="none"
    │
    ▼
SemanticEngineFactory (F27)
    │
    ├── resolves "none" → DeterministicSemanticEngine
    │
    ▼
DeterministicSemanticEngine
    │
    ├── uses markdown-it-py → AST
    ├── AST → Visitors → Observation[]
    ├── Observation[] → RuleEngine (rule packs) → ExtractedElement[]
    └── produces ExtractionResult
    │
    ▼
Evidence Graph layer (F05/F06)
```

---

## DeterministicSemanticEngine

Concrete implementation of `SemanticExtractionEngine` Protocol (F27).

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `extract` | `(documents: list[Document]) -> ExtractionResult` | `ExtractionResult` | Extract semantic elements using structural analysis |

**Configuration** (passed as `config` dict to factory):

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `max_heading_depth` | `int` | `6` | Maximum heading depth to process |
| `default_rule_pack` | `str \| Path` | built-in | Path to default rule pack YAML |
| `extra_rule_packs` | `list[str \| Path]` | `[]` | Additional rule pack paths |
| `default_confidence` | `float` | `0.70` | Default confidence for pattern-inferred elements |

**Behavioral Contracts**:
- MUST NOT modify input documents
- MUST be idempotent — same documents → same ExtractionResult (FR-011)
- MUST operate without network access or API keys (FR-002)
- MUST produce byte-identical output for identical inputs with identical rule packs

---

## Internal: ExtractionState

Mutable state passed through the visitor + rule engine pipeline.

| Field | Type | Description |
|-------|------|-------------|
| `heading_stack` | `list[str]` | Current heading hierarchy path |
| `observations` | `list[Observation]` | Structural observations collected by visitors |
| `elements` | `list[ExtractedElement]` | Final extracted elements (populated by rule engine) |

---

## Internal: Observation

A structural observation from an AST visitor, to be matched by rules.

| Field | Type | Description |
|-------|------|-------------|
| `type` | `str` | Observation type (e.g., `"heading"`, `"list_item"`, `"table_cell"`) |
| `content` | `str` | The observed text content |
| `context` | `dict` | Additional context (heading path, nesting level, parent section) |
| `location` | `tuple[str, str \| None]` | `(document_id, section_id)` — for evidence |

---

## ExtractionRule (Internal Model)

A rule definition in a rule pack.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique rule identifier |
| `name` | `str` | Yes | Human-readable rule name |
| `pattern` | `dict` | Yes | Pattern definition (keywords, heading, min_matches) |
| `type` | `Literal["fact", "entity", "relationship", "operation"]` | Yes | Semantic type this rule produces |
| `confidence` | `float` | Yes | Default confidence when this rule matches |
| `priority` | `int` | Yes | Numeric priority (1–100); higher wins on conflict |

**Conflict Resolution**: When multiple rules match the same observation, the rule with the highest `priority` wins. Ties broken by `id` lexicographic order (Q2).

---

## RulePack

A collection of ExtractionRules stored as an external YAML file.

| Property | Description |
|----------|-------------|
| Format | YAML with `rules` array |
| Location | `specmetrics/kernel/rules/` directory |
| Loading | `RulePackLoader` reads YAML, validates, returns `list[ExtractionRule]` |
| Merge | Built-in pack loaded first, extra packs merged; priority resolves conflicts |

---

## EvidenceReference (Extended for Deterministic Engine)

Extends the F27 canonical model with the extraction rule identifier.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `document_id` | `str` | Yes | Source document identifier (from F03 Document.id) |
| `section_id` | `str` | No | Section identifier from heading hierarchy (e.g., `"2.1"`) |
| `text` | `str` | Yes | Exact text fragment that supports the extracted element |
| `rule_id` | `str` | Yes | Identifier of the extraction rule that produced this element |

---

## ProcessingStats

Matches the F27 standard set (Q3).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `documents_processed` | `int` | Yes | Number of documents handled |
| `elements_extracted` | `int` | Yes | Total elements extracted |
| `elements_by_type` | `dict[str, int]` | Yes | Count of elements per semantic type |
| `duration_ms` | `int` | Yes | Processing time in milliseconds |
| `errors_count` | `int` | Yes | Number of documents that failed extraction |
