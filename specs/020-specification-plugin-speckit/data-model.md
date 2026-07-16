# Data Model: SpecKit Specification Adapter

## Overview

Data entities for the SpecKit Specification Adapter plugin. These models represent the adapter's internal structure for discovering, scanning, and normalizing SpecKit repository artifacts into the canonical `Document` model defined by F03.

## Entity Definitions

### SpecKitAdapter

Implements the `SpecificationAdapter` Protocol from F03.

| Method | Signature | Description |
|--------|-----------|-------------|
| `supports` | `(path: Path) -> bool` | Returns True if path has `.specify/`, `.specify/memory/constitution.md`, or `specs/` |
| `scan` | `(path: Path) -> ScanResult` | Discovers all artifacts and normalizes them |
| `scan_memory` | `(path: Path) -> list[Document]` | Discovers governance documents |
| `scan_features` | `(path: Path) -> list[Document]` | Discovers feature workspace artifacts |
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
| `governance_count` | `int` | Number of governance documents |
| `feature_count` | `int` | Number of feature workspaces |
| `specification_count` | `int` | Number of specification documents |
| `plan_count` | `int` | Number of plan documents |
| `tasks_count` | `int` | Number of tasks documents |
| `research_count` | `int` | Number of research documents |
| `data_model_count` | `int` | Number of data-model documents |
| `checklist_count` | `int` | Number of checklist documents |
| `unknown_count` | `int` | Number of unrecognized Markdown files |
| `duration_ms` | `int` | Total scan duration in milliseconds |

---

## Metadata Mapping

| SpecKit Artifact | Canonical document_type | Metadata.kind | Feature Source |
|---|---|---|---|
| `constitution.md` | constitution | governance | null |
| `spec.md` | specification | specification | Parent directory name |
| `plan.md` | plan | architecture | Parent directory name |
| `tasks.md` | tasks | implementation | Parent directory name |
| `research.md` | research | research | Parent directory name |
| `data-model.md` | data-model | data-model | Parent directory name |
| `checklists/**/*.md` | checklist | checklist | Parent's parent directory name |
| `*.md` (unrecognized) | unknown | unknown | Parent directory name |

### Field Derivation Rules

| Metadata Field | Derivation |
|----------------|------------|
| `framework` | Always `speckit` |
| `artifact_type` | From FR-005 mapping table |
| `kind` | From mapping table above |
| `feature` | For governance docs: null; for feature artifacts: the feature directory name under `specs/` |
| `workspace` | For governance: `.specify/memory`; for features: `specs/<feature>` |
| `relative_path` | Path relative to repository root |

## Discovery Rules

```
.specify/
    memory/
        constitution.md          # Governance document

specs/                           # Feature workspaces
    <feature>/
        spec.md                  # Feature specification
        plan.md                  # Architecture/planning (optional)
        tasks.md                 # Implementation tasks (optional)
        research.md              # Research (optional)
        data-model.md            # Data model (optional)
        checklists/              # Checkbooks (optional)
            **/*.md
        contracts/               # Interface contracts (optional — not scanned as documents)
        <any>.md                 # Unknown — included as document_type: unknown
```

### Document Identification

Format: `speckit:<artifact_type>:<relative-path>`

Examples:
- `speckit:constitution:.specify/memory/constitution.md`
- `speckit:specification:specs/001-add-user-authentication/spec.md`
- `speckit:plan:specs/001-add-user-authentication/plan.md`
- `speckit:tasks:specs/001-add-user-authentication/tasks.md`
- `speckit:checklist:specs/001-add-user-authentication/checklists/requirements.md`
- `speckit:unknown:specs/001-add-user-authentication/notes.md`
