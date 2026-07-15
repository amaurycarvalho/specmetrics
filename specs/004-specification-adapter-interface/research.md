# Research Report: Specification Adapter Plugin Interface

**Date**: 2026-07-15 | **Feature**: [spec.md](spec.md)

---

## 1. Adapter Interface Design: Protocol vs ABC

**Decision**: Use a `Protocol` class (structural subtyping) for the adapter
interface.

**Rationale**: Python Protocols enable static type checking without requiring
adapters to inherit from a base class. This is consistent with the F01
`EventHandler` Protocol used in `handler_registry.py`. Adapters simply need to
implement the required methods — no coupling to a base class hierarchy.

**Required methods**:
- `scan(repository_path: Path) -> list[Document]` — Discover and return all
  specification documents
- `supports(path: Path) -> bool` — Return True if this adapter can handle the
  given repository/directory

**Alternatives considered**:
- **Abstract Base Class (ABC)**: Would require inheritance, creating tighter
  coupling. Less Pythonic for plugin interfaces.
- **ABC with register(): `__init_subclass__`**: Automatically registers
  subclasses but introduces import-time side effects. Not suitable.

---

## 2. Document Type Taxonomy

**Decision**: Document types are advisory string labels, not a strict enum.
Adapters use heuristics to determine the type from the document's path,
content patterns, or framework conventions.

**Canonical type values** (recommended, not enforced):
| Type | Description |
|------|-------------|
| `"use_case"` | Functional use case or user story |
| `"business_rule"` | Business rule or policy |
| `"actor"` | Actor, persona, or stakeholder |
| `"process"` | Business process or workflow |
| `"data_group"` | Data entity or data structure |
| `"relationship"` | Relationship between entities |
| `"term"` | Glossary term or definition |
| `"section"` | General document section (fallback) |
| `"unknown"` | Unrecognized content |

**Rationale**: A strict enum would force every adapter to map every possible
document type, which would break when new SDD frameworks introduce novel
document types. String labels allow forward compatibility. F04 (Semantic
Extraction) is responsible for interpreting the type, not the adapter.

**Alternatives considered**:
- **Strict Enum**: Guarantees consistency but prevents extension. Not suitable
  for an open plugin ecosystem.
- **Type detection via pattern matching**: Adapters may use path patterns,
  frontmatter fields, or content analysis to determine type. Heuristics are
  adapter-specific.

---

## 3. Document Metadata Schema

**Decision**: Metadata is a free-form `dict[str, Any]` preserving
framework-specific information.

**Rationale**: Different SDD frameworks expose different metadata (e.g.,
OpenSpec has `spec_id` and `version`, SpecKit has `kind` and `scope`). A rigid
schema would lose framework-specific information. The free-form dict preserves
everything for downstream consumers (F04, F05) while keeping the core
`Document` model framework-agnostic.

**Expected common keys** (adapter-dependent):
- `title` — Document title
- `author` — Document author
- `version` — Document version
- `framework` — SDD framework name (e.g., "openspec", "speckit")
- `created_at` — Creation timestamp
- `updated_at` — Last update timestamp
- `section_depth` — Hierarchy level (for section-based documents)

---

## 4. Adapter Discovery via F02 PluginRegistry

**Decision**: Adapters use the existing F02 `PluginRegistry` with
`plugin_type=PluginType.ADAPTER`. A lightweight `AdapterRegistry` wrapper
provides adapter-specific lookup methods.

**Registration flow**:
1. F02 `load_plugins()` discovers the adapter via entry points
2. Adapter's factory function returns `PluginMetadata` with
   `plugin_type=PluginType.ADAPTER`
3. `PluginRegistry.install_handlers()` registers the adapter's event handlers
   (e.g., for `EventType.REPOSITORY_LOADED`)
4. `AdapterRegistry` wraps `PluginRegistry.get_by_type("adapter")` for
   adapter-specific queries

**Why a wrapper**: `PluginRegistry` is generic (handles all plugin types). The
`AdapterRegistry` provides convenience methods like `find_adapter(path)` that
call `supports()` on each registered adapter to find the right one for a given
repository.

---

## 5. Error Isolation Strategy

**Decision**: Document-level isolation — each document read is wrapped in a
try/except. A single malformed document never fails the entire scan.

**Pattern**:
```python
def scan(self, path: Path) -> list[Document]:
    documents = []
    for file_path in self._discover(path):
        try:
            doc = self._read_document(file_path)
            documents.append(doc)
        except Exception as exc:
            logger.warning("document_skipped", path=str(file_path), error=str(exc))
    return documents
```

This satisfies FR-005 (document read errors don't fail the scan).
