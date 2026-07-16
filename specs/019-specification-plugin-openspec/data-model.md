# Data Model: OpenSpec Specification Adapter

## Overview

Data entities for the OpenSpec Specification Adapter plugin. These models represent the adapter's internal structure for discovering, scanning, and normalizing OpenSpec repository artifacts into the canonical `Document` model defined by F03.

## Entity Definitions

### OpenSpecAdapter

Implements the `SpecificationAdapter` Protocol from F03.

| Method | Signature | Description |
|--------|-----------|-------------|
| `supports` | `(path: Path) -> bool` | Returns True if `path` contains `openspec/specs/` |
| `scan` | `(path: Path) -> ScanResult` | Discovers all artifacts and normalizes them |
| `scan_specs` | `(path: Path) -> list[Document]` | Discovers current specifications |
| `scan_changes` | `(path: Path) -> list[Document]` | Discovers change artifacts (active + archived) |
| `normalize_document` | `(file_path: Path, repo_root: Path) -> Document` | Normalizes one artifact into canonical Document |
| `build_metadata` | `(file_path: Path, repo_root: Path) -> dict` | Builds metadata from file path position |

---

### ScanResult

Container for the complete scan output.

| Field | Type | Description |
|-------|------|-------------|
| `documents` | `list[Document]` | All normalized documents from the scan |
| `errors` | `list[ScanError]` | Per-file errors encountered during scanning |
| `stats` | `ScanStats` | Summary statistics |
| `scanned_at` | `datetime` | Timestamp of scan completion |

---

### ScanError

A per-file error encountered during scanning.

| Field | Type | Description |
|-------|------|-------------|
| `file_path` | `str` | Relative path of the file that caused the error |
| `error_code` | `str` | Machine-readable error code |
| `message` | `str` | Human-readable error description |

---

### ScanStats

Summary statistics for a scan operation.

| Field | Type | Description |
|-------|------|-------------|
| `total_files_found` | `int` | Total files discovered on disk |
| `total_documents` | `int` | Total documents successfully normalized |
| `total_errors` | `int` | Total files that produced errors |
| `specification_count` | `int` | Number of specification documents |
| `proposal_count` | `int` | Number of proposal documents |
| `design_count` | `int` | Number of design documents |
| `tasks_count` | `int` | Number of tasks documents |
| `unknown_count` | `int` | Number of unrecognized Markdown files |
| `active_changes` | `int` | Number of active changes discovered |
| `archived_changes` | `int` | Number of archived changes discovered |
| `duration_ms` | `int` | Total scan duration in milliseconds |

---

## Metadata Mapping

| OpenSpec Artifact | Canonical document_type | Metadata.kind | Domain Source | Change Source |
|---|---|---|---|---|
| `specs/<domain>/spec.md` | specification | current-spec | Parent directory name | null |
| `proposal.md` | proposal | proposal | Change parent directory | Change directory name |
| `design.md` | design | design | Change parent directory | Change directory name |
| `tasks.md` | tasks | tasks | Change parent directory | Change directory name |
| `changes/<change>/specs/**/spec.md` | specification | delta-spec | Nested domain dir | Change directory name |

### Field Derivation Rules

| Metadata Field | Derivation |
|----------------|------------|
| `framework` | Always `openspec` |
| `repository_root` | Absolute path of the repository root |
| `artifact_type` | From FR-004 mapping table |
| `kind` | From mapping table above |
| `domain` | For specs: parent directory name under `specs/`; for changes: parent of the change directory |
| `change` | For change artifacts: the change directory name; for baseline specs: null |
| `status` | `archived` if path contains `changes/archive/`; otherwise `active` |
| `relative_path` | Path relative to repository root |

## Discovery Rules

```
openspec/
    specs/                          # Required — repository detection marker
        <domain>/
            spec.md                 # Current specification

    changes/                        # Optional
        <change>/                   # Active change
            proposal.md
            design.md
            tasks.md
            specs/
                <domain>/
                    spec.md         # Delta specification
        archive/                    # Optional
            <change>/               # Archived change
                (same structure as active)
```

### Exclusion Rules

The following directories and patterns are excluded from change discovery:
- `.git`
- `__pycache__`
- `.venv`
- `node_modules`
- `.specify`
- Any directory starting with `_`

### Document Identification

Format: `openspec:<artifact_type>:<relative-path>`

Examples:
- `openspec:specification:specs/auth/spec.md`
- `openspec:proposal:changes/add-user-authentication/proposal.md`
- `openspec:design:changes/add-user-authentication/design.md`
- `openspec:tasks:changes/add-user-authentication/tasks.md`
- `openspec:specification:changes/add-user-authentication/specs/api/spec.md`
- `openspec:unknown:specs/auth/readme.md`
