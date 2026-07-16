# Research: SpecKit Specification Adapter Plugin

## Overview

Researches the SpecKit repository layout, Specification Adapter Protocol integration, document normalization strategies, and feature metadata preservation patterns for the SpecMetrics SpecKit Adapter plugin. All ambiguity items from the clarify session have been resolved — this document validates technology choices and documents the adapter design.

## Technology Decisions

### Repository Detection Strategy

**Decision**: Detect SpecKit repositories by checking for any of three markers: `.specify/`, `.specify/memory/constitution.md`, or `specs/`. The `supports()` method performs lightweight `Path.exists()` checks without traversing the repository.

**Rationale**: FR-001 lists multiple detection markers. A repository may have only `.specify/` without `specs/` (governance-only), only `specs/` without `.specify/` (features-only), or both. Any single marker is sufficient for detection. The `Path.exists()` approach is O(1) per marker.

**Alternatives considered**: Requiring all markers (would miss valid SpecKit repos), scanning for `specs/` pattern (too expensive for `supports()`).

### Artifact Discovery Strategy

**Decision**: Two-phase discovery — scan `.specify/memory/` for governance documents (using `glob("**/*.md")`), then scan `specs/` for feature workspaces (listing subdirectories and globbing for recognized artifact filenames within each). Checklists use recursive `checklists/**/*.md` pattern.

**Rationale**: SpecKit separates governance from feature artifacts. Governance docs live in a fixed location and are always `.md` files. Feature workspaces are directories under `specs/` containing multiple artifact types. The recursive `checklists/**/*.md` pattern was clarified to support nested checklist subdirectories.

**Alternatives considered**: Single recursive scan (would not distinguish governance vs feature), filename-only filtering (would miss section hierarchy).

### Artifact Type Detection

**Decision**: Map filenames to document types using the table defined in FR-005. Unrecognized `.md` files receive `document_type: unknown`. The mapping is deterministic based on filename.

**Rationale**: The clarify session confirmed all `.md` files are included. Each recognized filename maps to a specific document type. Checklists use a glob pattern (`checklists/**/*.md`) to handle any filename under the checklists directory.

**Alternatives considered**: Content-based detection (violates FR-011 — must not interpret), extension-only detection (would miss type-specific metadata).

### Feature Metadata Preservation

**Decision**: Build metadata from the file's position in the directory tree. Governance documents under `.specify/memory/` have `feature: null` and `workspace: .specify/memory`. Feature artifacts under `specs/<feature>/` derive `feature` from the parent directory name and `workspace` from the full path.

**Rationale**: SpecKit encodes feature identity in the directory layout. Extracting this from path components is deterministic and requires no content parsing.

**Alternatives considered**: Parsing YAML front matter (violates FR-011), requiring a manifest file (increases spec authoring burden).

### Section Hierarchy Preservation

**Decision**: Parse Markdown ATX headings to build `DocumentSection` hierarchy. Each `#` through `######` heading creates a section node. Content between headings is attached to the preceding section.

**Rationale**: Consistent with the OpenSpec adapter and FR-010 requirements.

### Error Isolation

**Decision**: Per-file try/except — unreadable or malformed files generate document-level errors without interrupting the scan. The scan continues to the next file.

**Rationale**: FR-022, FR-023, and FR-024 all require error isolation with continued scanning.

### Observability

**Decision**: Emit structured INFO/ERROR log messages via structlog for scan start, completion, per-file errors, and artifact count summaries.

**Rationale**: Clarified during speckit.clarify — consistent with the OpenSpec adapter's observability contract.

## Integration Patterns

### Pipeline Event Flow

```
RepositoryLoaded (event) → Pipeline Engine requests scan from adapter
  → DocumentsDiscovered (event emitted by adapter) → pipeline context populated
```

The SpecKit adapter implements the `SpecificationAdapter` Protocol from F03. The Pipeline Engine calls `adapter.supports(path)` for adapter selection, then `adapter.scan(path)` for discovery.

### Relationship to Existing Specs

| Artifact | Relationship |
|----------|-------------|
| F02 (Plugin Discovery) | SpecKit Adapter registers via `specmetrics.plugins.adapter` entry point |
| F03 (Specification Adapter Interface) | Adapter implements the `SpecificationAdapter` Protocol |
| F04 (Semantic Extraction) | Consumes normalized `Document` objects produced by this adapter |
| F06 (Canonical Functional Model) | Built from documents discovered by this adapter |
