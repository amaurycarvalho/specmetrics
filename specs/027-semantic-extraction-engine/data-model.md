# Data Model: Semantic Extraction Engine

**Date**: 2026-07-17 | **Spec**: [spec.md](spec.md)

---

## Entity-Relationship Overview

```
Pipeline
    │
    ├── configures LLM provider
    │
    ▼
SemanticEngineFactory
    │
    ├── resolves provider → engine
    │
    ▼
SemanticExtractionEngine (Protocol)
    │
    ├── DeterministicSemanticEngine
    │   ├── uses markdown-it-py AST
    │   ├── visitors → observations
    │   ├── RuleEngine (rule packs)
    │   └── PatternLibrary
    │
    └── LiteLLMSemanticEngine
        ├── wraps LiteLLM gateway
        └── maps model response → ExtractionResult
    │
    ▼
ExtractionResult
    │
    ├── elements: list[ExtractedElement]
    ├── engine_id: str
    └── processing_stats: ProcessingStats
    │
    └── consumed by Evidence Graph layer
```

---

## SemanticExtractionEngine (Protocol)

Structural interface that every extraction engine must implement.

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `extract` | `(documents: list[Document]) -> ExtractionResult` | `ExtractionResult` | Extract semantic elements from one or more documents |

**Behavioral Contracts**:
- MUST NOT modify input documents
- MUST be idempotent — same documents + same state → same result (NFR-001)
- MUST produce `ExtractionResult` with all fields populated
- MUST preserve evidence references on every element (FR-010)
- MUST NOT expose engine implementation details in the result

---

## ExtractionResult

The canonical output model produced by both engines.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `elements` | `list[ExtractedElement]` | Yes | Extracted semantic elements |
| `engine_id` | `str` | Yes | Identifier of the engine that produced this result (`"deterministic"` or `"litellm"`) |
| `processing_stats` | `ProcessingStats` | Yes | Extraction statistics |

---

## ExtractedElement

A single semantic fact, entity, relationship, or operation identified during extraction.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Deterministic content-hash ID: `sha256("{doc_id}::{section_id}::{text}")[:16]` |
| `type` | `Literal["fact", "entity", "relationship", "operation"]` | Yes | Semantic type of the extracted element |
| `content` | `str` | Yes | The extracted semantic content as text |
| `confidence` | `float` | Yes | Confidence score (0.0–1.0). Deterministic engine uses RFC-031 table; LiteLLM engine derives from model logprobs |
| `evidence` | `EvidenceReference` | Yes | Source provenance for this element |

**Validation Rules**:
- `id` must be unique within a single `ExtractionResult`
- `type` must be one of the four defined semantic types
- `confidence` must be in range [0.0, 1.0]
- `evidence` must have a non-empty `document_id` and `text`

---

## EvidenceReference

A pointer back to the source material that justifies an extracted element.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `document_id` | `str` | Yes | Source document identifier (from F03 Document.id) |
| `section_id` | `str` | No | Section identifier within the document (null for whole-document elements) |
| `text` | `str` | Yes | Exact text fragment that supports the extracted element |

---

## ProcessingStats

Metadata about the extraction process for observability.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `documents_processed` | `int` | Yes | Number of documents handled |
| `elements_extracted` | `int` | Yes | Total elements extracted |
| `elements_by_type` | `dict[str, int]` | Yes | Count of elements per semantic type |
| `duration_ms` | `int` | Yes | Processing time in milliseconds |
| `errors_count` | `int` | Yes | Number of documents that failed extraction |

---

## SemanticEngineFactory

Factory that resolves LLM provider configuration to an engine implementation.

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `create` | `(provider: str, config: dict \| None = None) -> SemanticExtractionEngine` | Engine instance | Resolve provider string to engine — instantiated once per pipeline init |

**Resolution Table**:

| Provider | Engine |
|----------|--------|
| `"none"` | `DeterministicSemanticEngine(config)` |
| `"chatgpt"` | `LiteLLMSemanticEngine(model="gpt-4", ...)` |
| `"claude"` | `LiteLLMSemanticEngine(model="claude-3-opus", ...)` |
| `"gemini"` | `LiteLLMSemanticEngine(model="gemini-pro", ...)` |
| `"ollama"` | `LiteLLMSemanticEngine(model="ollama/llama3", ...)` |

---

## ExtractionRule

A definition in the rule library that recognizes a specific specification pattern.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique rule identifier |
| `name` | `str` | Yes | Human-readable rule name |
| `pattern` | `dict` | Yes | Pattern definition (headings, keywords, structure) |
| `type` | `Literal["fact", "entity", "relationship", "operation"]` | Yes | Semantic type this rule produces |
| `confidence` | `float` | Yes | Default confidence when this rule matches |
| `priority` | `int` | Yes | Numeric priority (1–100); higher wins on conflict |

**Conflict Resolution**: When multiple rules match the same observation, the rule with the highest `priority` wins. Ties broken by `id` lexicographic order.

---

## Internal: AST Visitor Model

Not part of public API but key to deterministic engine architecture.

```python
class ExtractionState:
    """Mutable state passed through the visitor + rule engine pipeline."""
    heading_stack: list[str]          # Current heading hierarchy
    observations: list[Observation]   # Structural observations collected by visitors
    elements: list[ExtractedElement]  # Final extracted elements

@dataclass
class Observation:
    """A structural observation from an AST visitor, to be matched by rules."""
    type: str                          # "heading", "list_item", "table_cell", etc.
    content: str                       # The observed text content
    context: dict                      # Additional context (heading path, nesting level, etc.)
    location: tuple[str, str | None]   # (document_id, section_id) — for evidence
```

---

## Internal: Engine Configuration

Configuration passed to each engine at initialization.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_heading_depth` | `int` | `6` | Maximum heading depth to process; deeper headings flattened |
| `default_rule_pack` | `str \| Path` | built-in | Path to default rule pack YAML file |
| `extra_rule_packs` | `list[str \| Path]` | `[]` | Additional rule pack paths to load |
| `confidence_default` | `float` | `0.70` | Default confidence for pattern-inferred elements |
