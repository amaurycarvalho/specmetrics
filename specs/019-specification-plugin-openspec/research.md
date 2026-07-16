# Research: OpenSpec Specification Adapter Plugin

## Overview

Researches the OpenSpec repository convention, Specification Adapter Protocol integration, document normalization strategies, and metadata preservation patterns for the SpecMetrics OpenSpec Adapter plugin. All ambiguity items from the clarify session have been resolved — this document validates technology choices and documents the adapter design.

## Technology Decisions

### Repository Detection Strategy

**Decision**: Detect OpenSpec repositories by checking for the existence of `openspec/` directory containing a `specs/` subdirectory. The `supports()` method performs a lightweight `Path.exists()` check without traversing the repository.

**Rationale**: FR-002 requires detection without scanning. The OpenSpec convention defines `openspec/specs/` as the root marker. This is a fast O(1) filesystem check. The `changes/` and `changes/archive/` directories are optional and may be absent.

**Alternatives considered**: Scanning for `openspec/` only (risk of false positives from unrelated directories), checking for `openspec/changes/` (optional, not reliable).

### Artifact Discovery Strategy

**Decision**: Use recursive glob patterns for specification discovery (`openspec/specs/**/spec.md`) and directory listing for change discovery (`openspec/changes/*/` with temp folder filtering). Each change directory is scanned for recognized artifact files (proposal.md, design.md, tasks.md) and delta specs under `changes/<change>/specs/**/spec.md`.

**Rationale**: The OpenSpec convention has well-defined directory layouts. Recursive glob is the most efficient pattern for `spec.md` discovery within specs/. Change discovery requires listing directories to identify individual changes, then scanning each for artifacts. Temp folder exclusions prevent false positives from VCS and build artifacts.

**Alternatives considered**: Walking the entire tree (slower, processes irrelevant files), requiring a manifest file (adds maintenance burden).

### Artifact Type Detection

**Decision**: Map filenames to document types using the table defined in FR-004. Unrecognized `.md` files receive `document_type: unknown`. The mapping is deterministic — filename determines type with no content inspection.

**Rationale**: Clarified during speckit.clarify — all `.md` files are included, unrecognized ones get `unknown` type. This ensures no artifacts are silently dropped while maintaining predictable behavior.

**Alternatives considered**: Content-based detection (violates FR-011 — must not interpret), extension-only detection (would miss type-specific metadata).

### Metadata Preservation

**Decision**: Build metadata from the file's position in the directory tree relative to the repository root. Spec documents under `openspec/specs/<domain>/spec.md` derive domain from the parent directory name. Change artifacts derive change ID from the change directory name and status from the presence of `archive/` in the path.

**Rationale**: The OpenSpec convention encodes structural metadata (domain, change, status) in the directory layout. Extracting this from path components is deterministic and requires no content parsing.

**Alternatives considered**: Parsing YAML front matter (violates FR-011), requiring a separate metadata file (increases spec authoring burden).

### Section Hierarchy Preservation

**Decision**: Parse Markdown headings to build `DocumentSection` hierarchy. Each `#` or `##` heading creates a section node. Content between headings is attached to the preceding section.

**Rationale**: FR-010 requires section hierarchy preservation. Markdown heading parsing is a well-understood problem with no ambiguity for standard ATX headings (`#` through `######`). This does not interpret content — it only identifies section boundaries.

**Alternatives considered**: Full AST parsing (over-engineered for section detection), line-based splitting (loses hierarchy).

### Error Isolation

**Decision**: Per-file try/except — unreadable or malformed files generate document-level errors without interrupting the scan. The scan continues to the next file. Errors are collected and returned as part of the scan result.

**Rationale**: FR-021 (unreadable files → document-level errors), FR-022 (malformed Markdown does not stop scanning), and FR-023 (scanning continues after failures) all require error isolation. The per-file approach is simple, predictable, and matches the project's existing patterns.

**Alternatives considered**: Fail-fast (violates FR-022/FR-023), batch processing (harder to isolate individual file errors).

### Observability

**Decision**: Emit structured INFO/ERROR log messages via structlog for scan start, completion, per-file errors, and artifact count summaries.

**Rationale**: Clarified during speckit.clarify — the adapter is a pure data transformation layer and does not require metrics emission. Structured logging provides sufficient observability for debugging and monitoring scan operations.

## Integration Patterns

### Pipeline Event Flow

```
RepositoryLoaded (event) → Pipeline Engine requests scan from adapter
  → DocumentsDiscovered (event emitted by adapter) → pipeline context populated
```

The OpenSpec adapter implements the `SpecificationAdapter` Protocol from F03. The Pipeline Engine calls `adapter.supports(path)` to select the correct adapter, then `adapter.scan(path)` to discover and normalize all documents.

### Relationship to Existing Specs

| Artifact | Relationship |
|----------|-------------|
| F02 (Plugin Discovery) | OpenSpec Adapter registers via `specmetrics.plugins.adapter` entry point |
| F03 (Specification Adapter Interface) | Adapter implements the `SpecificationAdapter` Protocol — `supports()` and `scan()` |
| F04 (Semantic Extraction) | Consumes normalized `Document` objects produced by this adapter |
| F06 (Canonical Functional Model) | Built from documents discovered by this adapter |
