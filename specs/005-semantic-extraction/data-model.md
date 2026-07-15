# Data Model: Semantic Extraction

**Date**: 2026-07-15 | **Spec**: [spec.md](spec.md)

---

## Entity-Relationship Overview

```
PipelineEngine (F01)
    │
    ├── publishes DOCUMENTS_DISCOVERED event
    │
    ▼
ExtractionStage (EventHandler)
    │
    ├── receives Document list (from F03 Adapter)
    ├── resolves provider via ProviderRouter
    │
    ▼
ExtractionProvider (Protocol — implemented per extraction strategy)
    │
    ├── extract(document) ──► ExtractionResult
    ├── supports_type(type) ──► bool
    │
    ▼
ExtractionResult
    │
    ├── elements: list[ExtractedElement]
    ├── provider_id: str
    ├── processing_stats: ProcessingStats
    │
    ▼
    └── published as SEMANTIC_EXTRACTION_COMPLETED event
        └── consumed by Evidence Graph (F05)
```

---

## ExtractedElement

A semantic element produced by extraction — represents a fact, entity, relationship, or operation identified in a specification document.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique identifier within the extraction result |
| `type` | `Literal["fact", "entity", "relationship", "operation"]` | Yes | Semantic type of the extracted element |
| `confidence` | `float` | Yes | Confidence score (0.0–1.0, where 1.0 is certain) |
| `evidence` | `EvidenceReference` | Yes | Source provenance for this element |
| `content` | `str` | Yes | The extracted semantic content as text |

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

## ExtractionResult

The output of a single provider's extraction for a single document.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `elements` | `list[ExtractedElement]` | Yes | Extracted semantic elements from the document |
| `provider_id` | `str` | Yes | Identifier of the extraction provider that produced this result |
| `processing_stats` | `ProcessingStats` | No | Metadata about the extraction process |

---

## ProcessingStats

Metadata about the extraction process for observability and debugging.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `documents_processed` | `int` | Yes | Number of documents handled by this provider |
| `elements_extracted` | `int` | Yes | Total elements extracted |
| `errors` | `int` | Yes | Number of documents that failed extraction |
| `duration_ms` | `int` | Yes | Processing time in milliseconds |

---

## ExtractionProvider (Protocol)

Structural interface that every extraction provider must implement.

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `extract` | `(document: Document) -> ExtractionResult` | `ExtractionResult` | Extract semantic elements from a single document |
| `supports_type` | `(document_type: str) -> bool` | `bool` | Return True if this provider can handle the given document type |

**Behavioral Contracts**:
- `extract()` MUST NOT modify the input document
- `extract()` MUST be idempotent — same document + same state → same result
- `extract()` MUST produce at least one element or return an empty list
- `supports_type()` MUST be fast (no full scan) — typically checks against a configured list
- Multiple providers with overlapping `supports_type()` are allowed; the first matching provider in configuration order is used

---

## ExtractionResult (Stage Output)

The consolidated output of the full extraction stage across all documents and providers.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `results` | `dict[str, ExtractionResult]` | Yes | Map of provider ID to per-document extraction results |
| `total_elements` | `int` | Yes | Total count of extracted elements across all providers |
| `documents_processed` | `int` | Yes | Total documents that were successfully processed |
| `documents_skipped` | `int` | Yes | Documents skipped due to errors or no matching provider |

---

## ProviderRouter

Configuration-driven router that maps document types to extraction providers.

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `resolve` | `(document_type: str) -> ExtractionProvider \| None` | Provider or None | Find the first provider that can handle the given document type |
| `register` | `(provider: ExtractionProvider, provider_id: str, types: list[str] \| None)` | `None` | Register a provider with optional type overrides |
