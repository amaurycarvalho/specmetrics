# Contract: Specification Adapter Interface

**Version**: 1.0.0 | **Date**: 2026-07-15 | **Spec**: [spec.md](../spec.md) | **Data Model**: [data-model.md](../data-model.md)

---

## Purpose

Defines the interface that every SDD framework adapter must implement. This
is a structural contract — adapters are not required to inherit from a base
class, but must provide these methods and return these types.

---

## Interface

### `supports(path: Path) -> bool`

Return `True` if this adapter can process the specification repository at
`path`.

**Rules**:
- MUST be fast — no full file scan. Check for framework markers (directory
  structure, config files, naming conventions).
- MUST NOT raise exceptions for non-matching directories (return `False`
  instead).
- SHOULD be deterministic — same `path` always returns the same result.

**Examples**:
```python
def supports(self, path: Path) -> bool:
    return (path / "specs").is_dir()
```

---

### `scan(repository_path: Path) -> list[Document]`

Discover all specification documents in the repository and return them as a
list of normalized `Document` objects.

**Rules**:
- MUST NOT modify the repository (read-only).
- MUST be idempotent.
- MUST NOT perform semantic interpretation of content.
- MUST handle individual file read errors without failing the entire scan.
  Skip the problematic file, log a warning, and continue.
- MUST return a list — empty list for repositories with no documents.
- MUST NOT raise exceptions for empty or non-existent repositories (return
  empty list and log a warning).
- SHOULD use path separators normalized to forward slashes.
- SHOULD use canonical document types (see data-model.md) when applicable.

**Return Type**: `list[Document]` (see [data-model.md](../data-model.md#Document))

---

## Integration with F02 Plugin Discovery

Adapters MUST register as SpecMetrics plugins per the F02 contract.

### Entry Point Registration

```toml
[project.entry-points."specmetrics.plugins"]
my-adapter = "my_adapter:register"
```

### Factory Function

```python
from specmetrics.kernel import PluginMetadata, PluginType, EventType

class MyAdapter:
    def supports(self, path) -> bool:
        return (path / "specs").is_dir()

    def scan(self, path) -> list:
        ...

def register() -> PluginMetadata:
    return PluginMetadata(
        id="my-adapter",
        api_version="1.0.0",
        plugin_type=PluginType.ADAPTER,
        handled_event_types=[EventType.REPOSITORY_LOADED],
        handler_factory=lambda: MyAdapter(),
    )
```

---

## Example: Minimal Adapter

```python
from pathlib import Path
from specmetrics.kernel import Document, SpecificationAdapter

class OpenSpecAdapter:
    """Adapter for OpenSpec SDD framework."""

    def supports(self, path: Path) -> bool:
        return (path / "specs").is_dir() and (path / "specs" / "index.yml").is_file()

    def scan(self, path: Path) -> list[Document]:
        documents = []
        specs_dir = path / "specs"
        if not specs_dir.is_dir():
            return documents

        for file_path in sorted(specs_dir.rglob("*.md")):
            try:
                rel_path = file_path.relative_to(path)
                doc = Document(
                    id=str(rel_path.with_suffix("")),
                    path=str(rel_path),
                    document_type=self._infer_type(file_path),
                    content=file_path.read_text(encoding="utf-8"),
                    metadata={"framework": "openspec"},
                )
                documents.append(doc)
            except Exception as exc:
                import logging
                logging.warning("Skipping %s: %s", file_path, exc)

        return documents

    def _infer_type(self, path: Path) -> str:
        parent = path.parent.name.lower()
        mapping = {
            "use-cases": "use_case",
            "business-rules": "business_rule",
            "actors": "actor",
            "processes": "process",
            "data": "data_group",
            "glossary": "term",
        }
        return mapping.get(parent, "unknown")
```

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Repository path does not exist | Return empty list, log warning |
| File is unreadable (permissions) | Skip file, log warning, continue |
| File is binary | Skip file, log warning, continue |
| File encoding error | Skip file, log warning, continue |
| `supports()` raises an exception | System treats as `False` |
| `scan()` raises a fatal error | Pipeline fails with StageError (handled by F01) |
