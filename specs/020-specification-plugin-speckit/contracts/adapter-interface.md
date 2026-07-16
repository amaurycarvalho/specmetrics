# Contract: Specification Adapter Interface (SpecKit)

## Overview

Defines the contract that the SpecKit Specification Adapter implements to integrate with the SpecMetrics Pipeline and Plugin Registry. This adapter normalizes SpecKit repository artifacts (governance documents and feature workspace files) into the canonical `Document` model.

## Discovery & Registration

### Entry Point Group

```text
specmetrics.plugins.adapter
```

The SpecKit adapter declares this entry point in `pyproject.toml`:

```toml
[project.entry-points."specmetrics.plugins.adapter"]
speckit = "specmetrics.plugins.adapter.speckit:SpecKitAdapter"
```

### Adapter Lifecycle

1. **Discovery**: Plugin Registry scans `specmetrics.plugins.adapter` entry points at startup
2. **Registration**: Adapter is registered with the `AdapterRegistry`
3. **Selection**: Pipeline Engine calls `adapter.supports(path)` on each registered adapter until one returns True
4. **Scanning**: Pipeline Engine calls `adapter.scan(path)` to discover and normalize all documents
5. **Teardown**: No persistent state — adapter instances are stateless per scan

## Interface Protocol

### `SpecificationAdapter`

```python
class SpecificationAdapter(Protocol):
    """Protocol that all specification adapter plugins must satisfy."""

    def supports(self, path: Path) -> bool:
        """Determine if this adapter supports the given repository path.
        
        Args:
            path: Absolute filesystem path to check.
        
        Returns:
            True if the path contains a repository following SpecKit conventions
            (at least one of: .specify/, .specify/memory/constitution.md, specs/).
            Must NOT perform a full scan — only lightweight checks.
        """

    def scan(self, path: Path) -> ScanResult:
        """Discover and normalize all specification artifacts.
        
        Args:
            path: Absolute path to the repository root.
        
        Returns:
            ScanResult containing all normalized Document objects, any
            per-file errors, and scan statistics.
        
        Raises:
            InvalidRepositoryError: If the path does not contain a valid
            repository for this adapter.
        """
```

### Output Contract

The `ScanResult` output must be consumable by:

| Downstream Consumer | Required Format | Contract |
|--------------------|-----------------|----------|
| Pipeline Engine | `ScanResult.documents` list | Each `Document` has `id`, `path`, `content`, `sections`, `metadata` per F03 |
| Semantic Extraction (F04) | Canonical `Document` model | `content` has raw Markdown; `sections` preserve heading hierarchy |
| CFM Builder (F06) | Canonical `Document` model | `metadata` contains framework, artifact_type, kind, feature, workspace |

### Metadata Contract

Every normalized `Document` MUST include at minimum:

```python
{
    "framework": "speckit",
    "artifact_type": str,         # From FR-005 mapping
    "kind": str,                  # governance, specification, architecture, implementation, research, data-model, checklist, unknown
    "feature": str | None,        # Feature directory name; null for governance docs
    "workspace": str,             # ".specify/memory" for governance; "specs/<feature>" for features
    "relative_path": str,         # Path relative to repository root
}
```

### Document Identification

Document IDs follow the format:
```text
speckit:<artifact_type>:<relative-path>
```

Example:
```text
speckit:specification:specs/001-add-user-authentication/spec.md
```

## Error Handling

Individual file failures MUST NOT interrupt the scan. Errors are collected and returned in `ScanResult.errors`:

```python
@dataclass
class ScanError:
    file_path: str        # Relative path of the failed file
    error_code: str       # "UNREADABLE", "PARSE_ERROR", "ENCODING_ERROR"
    message: str          # Human-readable description
```
