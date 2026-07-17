# Contract: Deterministic Semantic Engine Interface

**Version**: 1.0.0 | **Date**: 2026-07-17 | **Spec**: [spec.md](../spec.md) | **Data Model**: [data-model.md](../data-model.md)

---

## Purpose

Defines the interface for the DeterministicSemanticEngine — the offline implementation of the `SemanticExtractionEngine` Protocol (F27). This contract covers the engine's public interface (inherited from F27) and its internal component contracts.

---

## Public Interface (inherited from F27)

### `extract(documents: list[Document]) -> ExtractionResult`

Extract semantic elements from one or more specification documents using structural analysis.

**Rules**:
- MUST NOT modify input documents.
- MUST be idempotent — same documents always return the same result.
- MUST return an `ExtractionResult` with all fields populated.
- MUST include an `EvidenceReference` (with `document_id`, `section_id` where applicable, `text`, and `rule_id`) on every `ExtractedElement`.
- MUST assign content-hash IDs: `sha256(f"{document_id}::{section_path}::{text}")[:16]`.
- MUST NOT perform any network access, API calls, or AI service invocations.

**Return Type**: `ExtractionResult` (see [data-model.md](../data-model.md#ExtractionResult))

---

## Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `max_heading_depth` | `int` | `6` | Maximum heading depth to process; deeper headings flattened |
| `default_rule_pack` | `str \| Path` | built-in | Path to default rule pack YAML file |
| `extra_rule_packs` | `list[str \| Path]` | `[]` | Additional rule pack paths to load alongside built-in |
| `default_confidence` | `float` | `0.70` | Default confidence for pattern-inferred elements |

---

## Internal Component Contracts

### Visitor Protocol

Every AST visitor must provide:

```python
def visit(self, tokens: list[Token], state: ExtractionState) -> None: ...
```

**Rules**:
- MUST NOT modify the token list.
- MUST append observations to `state.observations` for matched content.
- MUST update `state.heading_stack` only for heading tokens.
- MUST handle empty token lists without raising exceptions.

### RulePackLoader

```python
class RulePackLoader:
    @staticmethod
    def load(path: str | Path) -> list[ExtractionRule]: ...
```

**Rules**:
- MUST parse YAML files with a `rules` array.
- MUST validate required fields: `id`, `name`, `pattern`, `type`, `confidence`, `priority`.
- MUST skip invalid rules with a logged warning.
- MUST raise `FileNotFoundError` for missing rule pack files.
- MUST raise `ValueError` for malformed YAML.

### PatternLibrary

```python
class PatternLibrary:
    def __init__(self, rule_packs: list[list[ExtractionRule]]): ...
    def match(self, observations: list[Observation]) -> list[ExtractedElement]: ...
```

**Rules**:
- MUST merge rules from all packs, resolving conflicts by highest priority (ties by rule ID).
- MUST return `ExtractedElement` for each matched observation, using the matching rule's `type`, `confidence`, and `id`.
- MUST assign content-hash IDs per the F27 canonical scheme.

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Empty document list | Return `ExtractionResult` with empty elements, zeroed stats |
| Document with no recognizable patterns | Return `ExtractionResult` with empty elements, processed count incremented |
| Unparseable document content | Create element with error content, increment error count, continue |
| Missing rule pack file | Log warning, fall back to built-in only |
| Rule pack with invalid entries | Skip invalid rules, log warning, continue with valid ones |
| Deeply nested headings (>max_heading_depth) | Flatten excess levels, log note |
| Binary/non-text content | Skip with logged warning, increment skipped count |
