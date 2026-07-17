# Research Report: Semantic Extraction Engine

**Date**: 2026-07-17 | **Feature**: [spec.md](spec.md)

---

## 1. Engine Interface: Protocol vs ABC

**Decision**: Use a `Protocol` class (structural subtyping) for `SemanticExtractionEngine`.

**Rationale**: Consistent with `ExtractionProvider` (005), `EventHandler` (F01), and `SpecificationAdapter` (F03) — all use Protocol. Structural subtyping allows any object with the right method signature to serve as an engine implementation without coupling to a base class hierarchy. `@runtime_checkable` is not needed; the factory creates instances that conform by construction.

**Required method**:
- `extract(documents: list[Document]) -> ExtractionResult`

**Alternatives considered**:
- **ABC**: Would require inheritance, creating tighter coupling. Less Pythonic for plugin-like interfaces.
- **Generic class with type var**: Over-engineered for a single-method interface.

---

## 2. Factory Pattern: Provider → Engine Resolution

**Decision**: `SemanticEngineFactory` with a static mapping from provider string to engine class.

**Rationale**: The provider-to-engine mapping is fixed per the spec (FR-002, FR-003, FR-004). A simple dict-based factory is the simplest correct implementation. The factory is instantiated once during pipeline initialization (NFR-002) and cached for the pipeline lifetime.

**Mapping**:

| Provider | Engine |
|----------|--------|
| `"none"` | `DeterministicSemanticEngine(config)` |
| `"chatgpt"` | `LiteLLMSemanticEngine(model="gpt-4", ...)` |
| `"claude"` | `LiteLLMSemanticEngine(model="claude-3-opus", ...)` |
| `"gemini"` | `LiteLLMSemanticEngine(model="gemini-pro", ...)` |
| `"ollama"` | `LiteLLMSemanticEngine(model="ollama/llama3", ...)` |

**Alternatives considered**:
- **Plugin-discovered engines**: Over-engineering for v1; the set of engines is known at compile time. Future engines can be added by extending the factory or making it plugin-based.
- **Configuration-file-driven**: Adds YAML/config parsing complexity for no benefit in v1.

---

## 3. Markdown AST Parsing

**Decision**: Use `markdown-it-py` (existing in constitution tech stack) to parse documents into AST.

**Rationale**: Already in the project's approved technology stack. Provides a rich AST with token types for headings, lists, tables, code blocks, blockquotes, emphasis, and links — covering all structure types required by FR-007.

**AST traversal**: The `markdown-it-py` token stream is a flat list of `Token` objects with nesting indicated by `Token.nesting` (+1 for open, 0 for self-closing, -1 for close). Visitors walk this stream maintaining heading hierarchy via a stack. This matches the flat-token-stream approach used by many markdown-it consumers.

**Alternatives considered**:
- **Regular expressions**: Explicitly rejected by RFC-031 ("Regular expressions are not the primary parsing mechanism"). Fragile for nested structures.
- **mistune**: Alternative Python markdown parser but not in the tech stack.

---

## 4. Visitor Pattern for AST Traversal

**Decision**: Implement dedicated visitor classes per RFC-031, each responsible for a single AST token type.

**Design**:
```python
class HeadingVisitor:
    """Collects heading hierarchy."""
    def visit(self, tokens: list[Token], state: ExtractionState) -> None:
        # Maintain heading level stack
        # Detect known section types (Actors, Business Rules, etc.)

class ListVisitor:
    """Collects list items."""
    def visit(self, tokens, state):
        # Extract ordered/unordered list items into candidates

class TableVisitor:
    """Collects table rows and headers."""

class CodeBlockVisitor:
    """Collects fenced code blocks with language annotation."""

class QuoteVisitor:
    """Collects blockquote content."""

class EmphasisVisitor:
    """Collects bold/italic text for term candidates."""

class LinkVisitor:
    """Collects hyperlinks and reference links."""
```

**Visitors included**: HeadingVisitor, ListVisitor, TableVisitor, ParagraphVisitor, CodeBlockVisitor, QuoteVisitor, EmphasisVisitor, LinkVisitor — matching FR-007 requirements.

**Alternatives considered**:
- **Single monolithic visitor**: Violates Single Responsibility and would be harder to extend with new structure types.

---

## 5. Rule Engine Design

**Decision**: Rule engine operates as a two-phase pipeline: (1) structural observations from visitors → (2) rule matching transforms observations into typed semantic elements.

**Rule format** (external YAML):
```yaml
rules:
  - id: "user-story"
    name: "User Story"
    pattern:
      heading: "User Story" | "User Stories"
    type: "entity"
    confidence: 0.95
    priority: 80

  - id: "gwt"
    name: "Given/When/Then"
    pattern:
      keywords: ["Given", "When", "Then"]
      min_matches: 2
    type: "fact"
    confidence: 0.85
    priority: 70

  - id: "requirement-shall"
    name: "Requirement Statement"
    pattern:
      keywords: ["Must", "Shall", "Should"]
    type: "fact"
    confidence: 0.70
    priority: 60
```

**Engine flow**:
```
AST Token Stream → Visitors → Observations[]
Observations[] → Rule Engine (match rules by priority) → ExtractedElement[]
```

**Conflict resolution**: When multiple rules match the same observation, the rule with the highest `priority` score wins (per Q3 clarification). Ties are broken by rule id lexicographic order.

**Alternatives considered**:
- **Regex-based pattern matching**: Rejected by RFC-031. AST-aware matching is more robust.
- **DSL for rules**: Over-engineered for v1. YAML-based rules with structured pattern fields are sufficient.

---

## 6. Pattern Library

**Decision**: Implement built-in pattern matchers corresponding to FR-008 rule types, organized as a `PatternLibrary` class that loads from rule packs and provides `match(observations) -> list[ExtractedElement]`.

**Standard patterns** (to be included as the default rule pack file):
- User Story (`As a... I want... So that...`)
- Given/When/Then
- Requirement statements (shall, must, should, will)
- Business Rules (If... Then...)
- Actors (heading-based detection)
- Constraints
- Assumptions
- Decisions
- Glossary Terms

**Alternatives considered**:
- **Hardcoded matchers in visitor code**: Violates Rule Externalization (Principle IX). Keeping patterns as external rule packs allows users to extend without modifying engine source.

---

## 7. Confidence Model

**Decision**: Deterministic confidence values as defined by RFC-031.

| Source | Confidence |
|--------|------------|
| Explicit heading match | 1.00 |
| Framework convention (heading + known section type) | 0.95 |
| Structural heuristic (indentation, bullet level) | 0.85 |
| Pattern inference (keyword match, GWT structure) | 0.70 |
| LiteLLM logprob-derived (from Q4) | 0.0–1.0 per model |

**Note**: LiteLLM engine confidence is independent of the deterministic table — it reflects the model's own uncertainty via token logprobs. Both are mapped to the same 0.0–1.0 scale for model compatibility.

---

## 8. Evidence Reference Model

**Decision**: Every `ExtractedElement` carries an `EvidenceReference` with `document_id`, `section_id` (optional), and `text` (the exact source fragment).

**Fields**:
| Field | Type | Required | Source |
|-------|------|----------|--------|
| `document_id` | `str` | Yes | F03 Document.id (inherited from 005 model) |
| `section_id` | `str \| None` | No | Derived from heading hierarchy (e.g., `"2.1"`) |
| `text` | `str` | Yes | Exact text fragment that supports the element |

**Content-hash ID** (per Q2): `sha256(f"{document_id}::{section_id or ''}::{text}")[:16]` — producing a deterministic 16-character hex ID.

---

## 9. LiteLLM Integration for LLM Engine

**Decision**: `LiteLLMSemanticEngine` wraps the existing LiteLLM `completion()` call, sending structured prompts to extract semantic elements from document text.

**Design**:
- Document text + structure hints (heading hierarchy as context) → LLM prompt
- LLM response → structured JSON → `ExtractionResult`
- Evidence references mapped back to source document locations
- Confidence derived from logprobs where available; default 0.85 if unavailable

**Failure behavior** (per Q1): If the provider is unavailable, the engine raises a structured error (does not silently fall back to deterministic). Pipeline handles the error via FR-012.

**Alternatives considered**:
- **Direct provider integration**: Would require separate code for each LLM provider. LiteLLM provides a unified interface.
- **Reuse existing llm_provider.py**: The existing provider is designed for the ExtractionProvider plugin system. The LiteLLMSemanticEngine is a new higher-level abstraction that could wrap it or use LiteLLM directly.

---

## 10. Extraction Statistics Model

**Decision** (per Q5): Standard set of statistics reported in `ExtractionResult.processing_stats`.

| Field | Type | Description |
|-------|------|-------------|
| `documents_processed` | `int` | Number of documents handled |
| `elements_extracted` | `int` | Total elements extracted |
| `elements_by_type` | `dict[str, int]` | Count of elements per semantic type |
| `duration_ms` | `int` | Processing time in milliseconds |
| `errors_count` | `int` | Number of documents that failed extraction |

This extends the existing `ProcessingStats` model from 005 with the `elements_by_type` field.
