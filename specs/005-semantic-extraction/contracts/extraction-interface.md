# Contract: Extraction Provider Interface

**Version**: 1.0.0 | **Date**: 2026-07-15 | **Spec**: [spec.md](../spec.md) | **Data Model**: [data-model.md](../data-model.md)

---

## Purpose

Defines the interface that every extraction provider must implement. This is a structural contract — providers are not required to inherit from a base class, but must provide these methods and return these types.

---

## Interface

### `extract(document: Document) -> ExtractionResult`

Extract semantic elements from a single specification document.

**Rules**:
- MUST NOT modify the input document.
- MUST be idempotent — same document always returns the same result.
- MUST return an `ExtractionResult` — empty `elements` list for documents with no recognizable semantic content.
- SHOULD produce at least one `ExtractedElement` per meaningful section, fact, entity, or relationship.
- MUST handle internal errors without raising exceptions to the caller (return result with empty elements and populate error count in stats).

**Return Type**: `ExtractionResult` (see [data-model.md](../data-model.md#ExtractionResult))

---

### `supports_type(document_type: str) -> bool`

Return `True` if this provider can extract semantic elements from documents of the given type.

**Rules**:
- MUST be fast — no full document scan or external calls.
- MUST NOT raise exceptions for unknown types (return `False` instead).
- SHOULD be deterministic — same `document_type` always returns the same result.

---

## Integration with F02 Plugin Discovery

Providers MUST register as SpecMetrics plugins per the F02 contract, with `plugin_type=PluginType.SEMANTIC`.

### Entry Point Registration

```toml
[project.entry-points."specmetrics.plugins"]
my-provider = "my_provider:register"
```

### Factory Function

```python
from specmetrics.kernel import PluginMetadata, PluginType
from specmetrics.kernel.extraction_provider import ExtractionProvider, ExtractionResult

class MyProvider:
    def extract(self, document) -> ExtractionResult:
        ...

    def supports_type(self, document_type: str) -> bool:
        return document_type in ("use_case", "business_rule")

def register() -> PluginMetadata:
    return PluginMetadata(
        id="my-provider",
        api_version="1.0.0",
        plugin_type=PluginType.SEMANTIC,
        handler_factory=lambda: MyProvider(),
    )
```

Configure routing in the extraction configuration:

```yaml
extraction:
  routing:
    "use_case": "my-provider"
    "business_rule": "my-provider"
    "*": "llm-provider"  # default fallback
```

---

## Example: Minimal Provider

```python
from specmetrics.kernel import Document
from specmetrics.kernel.extraction_provider import (
    ExtractionProvider,
    ExtractionResult,
    ExtractedElement,
    EvidenceReference,
)

class UseCaseProvider:
    def supports_type(self, document_type: str) -> bool:
        return document_type == "use_case"

    def extract(self, document: Document) -> ExtractionResult:
        elements = []
        for section in (document.sections or []):
            elements.append(ExtractedElement(
                id=f"{document.id}/{section.id}",
                type="fact",
                confidence=0.95,
                evidence=EvidenceReference(
                    document_id=document.id,
                    section_id=section.id,
                    text=section.content,
                ),
                content=f"Use case {section.title}: {section.content}",
            ))
        return ExtractionResult(
            elements=elements,
            provider_id="use-case-provider",
            processing_stats=ProcessingStats(
                documents_processed=1,
                elements_extracted=len(elements),
                errors=0,
                duration_ms=42,
            ),
        )
```

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Document type not supported by any provider | Skip document, log warning, continue |
| Provider raises an unexpected exception | Log error, skip document, continue pipeline |
| LLM provider unavailable (API/network error) | Degrade to structural parsing, log warning |
| Document has no recognizable semantic content | Return empty elements list |
| `supports_type()` raises an exception | System treats as `False` |
