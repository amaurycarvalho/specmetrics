# Research Report: Semantic Extraction

**Date**: 2026-07-15 | **Feature**: [spec.md](spec.md)

---

## 1. Extraction Provider Interface: Protocol vs ABC

**Decision**: Use a `Protocol` class (structural subtyping) for the extraction provider interface.

**Rationale**: Consistent with F01 `EventHandler` and F03 `SpecificationAdapter` Protocol patterns already established in the project. Providers simply implement the required methods — no coupling to a base class hierarchy. The `@runtime_checkable` decorator is not needed; duck typing via `hasattr` checks in the registry (following the F03 pattern) avoids isinstance restrictions.

**Required methods**:
- `extract(document: Document) -> ExtractionResult` — Extract semantic elements from a single document
- `supported_type(document_type: str) -> bool` — Return True if this provider can handle the given document type

**Alternatives considered**:
- **Abstract Base Class (ABC)**: Would require inheritance, creating tighter coupling. Less Pythonic for plugin interfaces.
- **Base class with registry via `__init_subclass__`**: Automatically registers subclasses but introduces import-time side effects. Not suitable.

---

## 2. ExtractionResult Data Model

**Decision**: Use Pydantic v2 models (matching the constitution tech stack) for ExtractionResult and ExtractedElement.

**Rationale**: Pydantic v2 is already in the project tech stack and provides:
- Immutable data with validation (matching PipelineEvent frozen dataclass pattern)
- Serialization to dict/JSON for pipeline event payloads
- Clear field types and defaults

**Core types**:
- `ExtractedElement`: id (str), type (Literal["fact", "entity", "relationship", "operation"]), confidence (float, 0.0-1.0), evidence (EvidenceReference), content (str)
- `EvidenceReference`: document_id (str), section_id (str | None), text (str)
- `ExtractionResult`: elements (list[ExtractedElement]), provider_id (str), processing_stats (ProcessingStats)
- `ProcessingStats`: documents_processed (int), elements_extracted (int), errors (int), duration_ms (int)

---

## 3. LLM Provider Integration

**Decision**: Use LiteLLM (existing dependency) as the LLM gateway for the built-in provider.

**Rationale**: LiteLLM is already in the project's tech stack and provides a unified interface across multiple LLM backends (OpenAI, Anthropic, local models via Ollama/vLLM). This allows the built-in provider to work out of the box with at least one free backend and be configured for others.

**Graceful degradation strategy**:
- If LLM is unavailable (no API key, network error, rate limit): return extraction result with structural parsing only (section headers, frontmatter fields, list items)
- Log the degradation reason and continue pipeline execution
- User can configure a fallback provider in the routing config

---

## 4. Provider Routing Strategy

**Decision**: Document-type string matching against provider-declared supported types, with configurable routing table.

**Rationale**: The F03 `Document` model has a `document_type` string field (e.g., "use_case", "business_rule", "section"). Each `ExtractionProvider` declares which types it supports. The routing logic:
1. Check routing config for explicit provider-to-type mappings
2. If no config match, iterate registered providers in order, calling `supports_type()`
3. Use the first provider that returns True
4. If no provider matches, log warning and skip the document

This matches the F03 `AdapterRegistry.find_adapter()` pattern.

---

## 5. Pipeline Stage Integration

**Decision**: Implement extraction as a PipelineEvent handler registered for `EventType.DOCUMENTS_DISCOVERED`.

**Rationale**: The existing pipeline architecture (F01) uses event-driven stages. `ExtractionStage` implements the `EventHandler` Protocol:
- `handled_event_type` → `EventType.DOCUMENTS_DISCOVERED`
- `handler_id` → `"extraction_stage"`
- `stage_name` → `"semantic_extraction"`
- `handle(event)` → consumes DocumentsDiscovered payload, produces ExtractionResult, publishes `SEMANTIC_EXTRACTION_COMPLETED` event

This matches the pipeline pattern established in F01 and used by all other stages.

---

## 6. Error Isolation Strategy

**Decision**: Per-document isolation — each document is processed independently within the extraction stage.

**Pattern**:
```python
def handle(self, event: PipelineEvent) -> PipelineContext:
    documents = event.payload.get("documents", [])
    all_elements = []
    for doc in documents:
        try:
            provider = self._router.resolve(doc.document_type)
            if provider is None:
                logger.warning("no_provider_for_document", doc_id=doc.id, doc_type=doc.document_type)
                continue
            result = provider.extract(doc)
            all_elements.extend(result.elements)
        except Exception as exc:
            logger.warning("document_extraction_failed", doc_id=doc.id, error=str(exc))
    return self._build_context(event, all_elements)
```

This satisfies FR-004 (per-document error isolation).
