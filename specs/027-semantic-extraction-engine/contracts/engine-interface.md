# Contract: Semantic Extraction Engine Interface

**Version**: 1.0.0 | **Date**: 2026-07-17 | **Spec**: [spec.md](../spec.md) | **Data Model**: [data-model.md](../data-model.md)

---

## Purpose

Defines the interface that every semantic extraction engine must implement. The Pipeline Engine interacts exclusively through this interface — it never depends on a specific engine implementation. This contract is internal to the kernel and is not exposed to plugin developers (who implement `ExtractionProvider` instead).

---

## Responsibilities

### The engine IS responsible for:

- **Semantic extraction**: Transforming normalized specification documents into canonical semantic elements.
- **Evidence preservation**: Every extracted element MUST carry an `EvidenceReference` with document ID, section identifier, and source text fragment.
- **Confidence generation**: Assigning a deterministic confidence score (0.0–1.0) to each extracted element per the engine's confidence model.
- **Extraction statistics**: Reporting processing metadata including documents processed, elements extracted, elements by type, duration, and errors count.
- **Deterministic output model**: Producing an `ExtractionResult` conforming to the canonical model defined in [data-model.md](../data-model.md).

### The engine is NOT responsible for:

- **Provider configuration**: Engine does not manage API keys, model selection, or provider authentication. These are configured at the pipeline level and passed to the factory.
- **Pipeline orchestration**: Engine does not control pipeline flow, event publishing, or stage sequencing. It is a single stage invoked by the Pipeline Engine.
- **Graph construction**: Engine does not build the evidence graph or manage graph persistence. It produces `ExtractionResult` consumed by the Evidence Graph layer.

---

## Interface

### `extract(documents: list[Document]) -> ExtractionResult`

Extract semantic elements from one or more specification documents.

**Rules**:
- MUST NOT modify input documents.
- MUST be idempotent — same documents always return the same result (for deterministic engine; LiteLLM engine result may vary with model version).
- MUST return an `ExtractionResult` — empty `elements` list for documents with no recognizable semantic content.
- MUST populate all fields in `ExtractionResult`, `ExtractedElement`, and `ProcessingStats`.
- MUST include an `EvidenceReference` with non-empty `document_id` and `text` on every `ExtractedElement`.
- MUST NOT expose engine implementation details (e.g., internal state, model names) in the output.
- MUST generate deterministic content-hash IDs for each element: `sha256(f"{document_id}::{section_path}::{text}")[:16]`.
- When an LLM provider is unavailable: the `LiteLLMSemanticEngine` MUST raise a structured error — it MUST NOT silently fall back to deterministic extraction.

**Return Type**: `ExtractionResult` (see [data-model.md](../data-model.md#ExtractionResult))

---

## Factory

### `SemanticEngineFactory.create(provider: str, config: dict | None = None) -> SemanticExtractionEngine`

Resolve a provider string to an engine implementation.

**Rules**:
- MUST be called once during pipeline initialization (NFR-002).
- MUST return a fully configured engine instance.
- MUST raise `ValueError` for unknown provider strings.
- The returned engine MUST be stateless and safe for concurrent use (if multiple pipeline runs share the instance).

**Resolution Table**:

| `provider` | Engine Class |
|------------|-------------|
| `"none"` | `DeterministicSemanticEngine` |
| `"chatgpt"` | `LiteLLMSemanticEngine` |
| `"claude"` | `LiteLLMSemanticEngine` |
| `"gemini"` | `LiteLLMSemanticEngine` |
| `"ollama"` | `LiteLLMSemanticEngine` |

---

## Configuration

The engine interface accepts a configuration dict at construction. Engine implementations MAY define their own configuration schema as long as it remains compatible with the public contract.

### DeterministicSemanticEngine Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `max_heading_depth` | `int` | `6` | Maximum heading depth to analyze |
| `rule_packs` | `list[str]` | built-in | Paths to rule pack YAML files |
| `default_confidence` | `float` | `0.70` | Default confidence for pattern-inferred elements |

### LiteLLMSemanticEngine Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `model` | `str` | (required) | LiteLLM model identifier (e.g., `"gpt-4"`, `"claude-3-opus"`) |
| `api_key` | `str \| None` | `None` | API key for the provider |
| `temperature` | `float` | `0.0` | LLM generation temperature |
| `max_tokens` | `int` | `4096` | Maximum tokens in LLM response |

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Unknown provider string | `SemanticEngineFactory.create()` raises `ValueError` |
| LLM provider authentication failure | `LiteLLMSemanticEngine.extract()` raises structured error; pipeline handles per FR-012 |
| LLM provider timeout | Same as above — fail cleanly, no silent fallback |
| LLM provider rate limited | Same as above |
| Document list is empty | Return `ExtractionResult` with empty elements and zeroed stats |
| Malformed document (unparseable) | Return element with error content, increment error count |

---

## Example: Pipeline Integration

```python
from specmetrics.kernel.semantic_extraction_engine import SemanticEngineFactory
from specmetrics.kernel.adapter_interface import Document

# Pipeline initialization — once
config = {"provider": "none"}
engine = SemanticEngineFactory.create(config["provider"])

# Pipeline execution — per run
documents: list[Document] = adapter.discover()
result = engine.extract(documents)
# result: ExtractionResult with elements, evidence, stats
```
