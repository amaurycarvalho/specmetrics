# Feature Specification: Specification Plugin — OpenSpec

**Feature Branch**: `019-specification-plugin-openspec`

**Created**: 2026-07-16

**Status**: Draft

**Input**: User description: "OpenSpec Specification Adapter Plugin"

---

# Overview

The OpenSpec Specification Plugin implements the **Specification Adapter Plugin Interface (F03)** for repositories that follow the OpenSpec convention.

Its responsibility is exclusively to:

- detect OpenSpec repositories;
- discover specification artifacts;
- normalize them into the canonical `Document` model;
- preserve structural metadata for downstream semantic processing.

The plugin **does not interpret requirements**, calculate functional size, or merge delta specifications. Those responsibilities belong to later pipeline stages.

The adapter supports both the **current specification baseline (`specs/`)** and **active change proposals (`changes/`)**, exposing every artifact as an independent canonical document.

---

# User Scenarios & Testing

## User Story 1 — Discover current specifications (Priority: P1)

A repository contains an OpenSpec project with multiple domains under `openspec/specs/`.

The adapter discovers every specification document and exposes them to the pipeline.

**Why this priority**

The current specification baseline is the primary source of truth for semantic extraction.

**Independent Test**

Provide an OpenSpec repository containing multiple domains and verify every `spec.md` is discovered.

### Acceptance Scenarios

1. **Given** an OpenSpec repository

   **When** the adapter scans `openspec/specs`

   **Then** every `spec.md` is returned as a normalized Document.

2. **Given** nested specification domains

   **When** scanning

   **Then** every domain specification is discovered.

3. **Given** an empty `specs/`

   **When** scanning

   **Then** an empty specification list is returned without error.

---

## User Story 2 — Discover active changes (Priority: P1)

A project contains multiple active OpenSpec changes.

The adapter discovers all change artifacts independently.

**Why this priority**

Changes represent future system behavior and must participate in semantic analysis.

**Independent Test**

Create two active changes and verify all proposal, design, tasks and delta specs are returned.

### Acceptance Scenarios

1. **Given** two active change folders

   **When** scanning

   **Then** both changes are discovered.

2. **Given** a change containing proposal, design, tasks and delta specs

   **When** scanning

   **Then** every artifact becomes an individual Document.

3. **Given** an archived change

   **When** scanning

   **Then** it is marked as archived in metadata.

---

## User Story 3 — Preserve OpenSpec metadata (Priority: P1)

The adapter exposes OpenSpec-specific metadata without interpreting it.

**Why this priority**

Later semantic stages need repository context for traceability.

**Independent Test**

Verify metadata is preserved exactly as represented by the repository structure.

### Acceptance Scenarios

1. **Given** a specification document

   **When** normalized

   **Then** metadata contains the domain name.

2. **Given** a change artifact

   **When** normalized

   **Then** metadata contains the change identifier.

3. **Given** an archived change

   **When** normalized

   **Then** metadata indicates archived status.

---

## User Story 4 — Detect OpenSpec repositories (Priority: P1)

The Plugin Registry evaluates installed adapters.

The OpenSpec adapter determines whether a repository follows the OpenSpec convention.

**Why this priority**

The pipeline must automatically select the proper adapter.

**Independent Test**

Verify `supports()` returns True only for valid OpenSpec repositories.

### Acceptance Scenarios

1. **Given** an OpenSpec repository

   **When** `supports()` executes

   **Then** True is returned.

2. **Given** a non-OpenSpec repository

   **When** `supports()` executes

   **Then** False is returned.

---

# Edge Cases

- Missing `changes/` directory.
- Missing `specs/` directory.
- Empty change folders.
- Missing optional artifacts (`design.md`, `tasks.md`).
- Duplicate domain names.
- Invalid Markdown.
- Large repositories (>1000 documents).
- Symbolic links.
- Corrupted UTF-8 files.
- Repository containing both archived and active changes.

---

# Constitution Check

## Engaged Principles

- **Specification First**
- **Canonical Representation**
- **Plugin-Oriented Architecture**
- **Traceability**
- **Deterministic Processing**

## Compliance Notes

The plugin never performs semantic interpretation.

It simply transforms OpenSpec filesystem artifacts into canonical `Document` objects.

---

# Requirements

## Functional Requirements

### Repository Detection

**FR-001**

The plugin MUST detect OpenSpec repositories using the following markers:

- `openspec/`
- `openspec/specs/`

---

**FR-002**

The plugin MUST expose

```python
supports(repository_path)
```

without scanning the repository.

---

### Repository Scan

**FR-003**

The adapter MUST discover:

- current specifications
- active changes
- archived changes

---

**FR-004**

Every Markdown artifact MUST become one canonical Document.

Supported artifacts include:

| Artifact    | Document Type |
| ----------- | ------------- |
| spec.md     | specification |
| proposal.md | proposal      |
| design.md   | design        |
| tasks.md    | tasks         |

---

**FR-005**

The adapter MUST recursively discover:

```
openspec/specs/**/spec.md
```

---

**FR-006**

The adapter MUST recursively discover

```
openspec/changes/*/
```

excluding implementation-specific temporary folders.

---

**FR-007**

Archived changes inside

```
openspec/changes/archive/
```

MUST also be discovered.

---

### Normalization

**FR-008**

Every discovered artifact MUST be normalized into the canonical `Document` model.

---

**FR-009**

The adapter MUST preserve raw Markdown.

---

**FR-010**

The adapter MUST preserve section hierarchy using `DocumentSection`.

---

**FR-011**

The adapter MUST NOT interpret:

- Requirements
- Scenarios
- ADDED
- MODIFIED
- REMOVED
- Acceptance Criteria

Those remain raw content.

---

### Metadata

**FR-012**

Every Document MUST include metadata.

Minimum metadata:

```yaml
framework: openspec
repository_root:
artifact_type:
domain:
change:
status:
relative_path:
```

---

**FR-013**

Specification documents MUST include

```yaml
kind: current-spec
```

---

**FR-014**

Delta specifications MUST include

```yaml
kind: delta-spec
```

---

**FR-015**

Proposal documents MUST include

```yaml
kind: proposal
```

---

**FR-016**

Design documents MUST include

```yaml
kind: design
```

---

**FR-017**

Tasks documents MUST include

```yaml
kind: tasks
```

---

**FR-018**

Archived documents MUST contain

```yaml
status: archived
```

otherwise

```yaml
status: active
```

---

### Plugin Registration

**FR-019**

The plugin MUST register using the Specification Adapter Entry Point defined by F03.

---

**FR-020**

Plugin metadata SHALL include

- plugin id
- plugin version
- supported framework
- supported artifact types

---

### Error Handling

**FR-021**

Unreadable files SHALL generate document-level errors.

---

**FR-022**

Malformed Markdown SHALL NOT stop repository scanning.

---

**FR-023**

Scanning SHALL continue after individual failures.

---

# Key Entities

## OpenSpec Repository

A repository organized according to the OpenSpec convention.

---

## Specification Domain

A directory located under

```
openspec/specs/
```

representing one functional domain.

Example

```
specs/auth/
specs/api/
specs/payment/
```

---

## Change

A proposed modification represented by one directory under

```
changes/
```

---

## Delta Specification

A specification inside

```
changes/<change>/specs/
```

representing proposed additions, modifications or removals.

---

## OpenSpec Artifact

One Markdown document belonging to the OpenSpec lifecycle.

Possible artifact kinds:

- specification
- proposal
- design
- tasks

---

# Success Criteria

**SC-001**

Repositories with 500 Markdown artifacts are scanned in under 5 seconds.

---

**SC-002**

100% of valid OpenSpec artifacts are normalized.

---

**SC-003**

Malformed documents do not interrupt scanning.

---

**SC-004**

The adapter correctly distinguishes:

- baseline specifications
- active changes
- archived changes

---

**SC-005**

Every normalized document is directly consumable by the Semantic Extraction Engine without OpenSpec-specific logic.

---

# Assumptions

- OpenSpec repositories follow the published folder convention.
- Markdown is UTF-8 encoded.
- Delta merging is outside the adapter scope.
- Semantic interpretation is outside the adapter scope.
- Repository checkout has already occurred.
- The adapter is stateless.

---

# Data Model

## OpenSpecAdapter

Implements the `SpecificationAdapter` protocol.

```
OpenSpecAdapter
    ├── supports(path)
    ├── scan(path)
    ├── scan_specs()
    ├── scan_changes()
    ├── normalize_document()
    └── build_metadata()
```

---

## Metadata Mapping

| OpenSpec Artifact  | Canonical document_type | Metadata.kind |
| ------------------ | ----------------------- | ------------- |
| specs/\*/spec.md   | specification           | current-spec  |
| proposal.md        | proposal                | proposal      |
| design.md          | design                  | design        |
| tasks.md           | tasks                   | tasks         |
| changes/\*/spec.md | specification           | delta-spec    |

---

## Canonical Metadata Example

```yaml
framework: openspec
artifact_type: specification
kind: delta-spec
domain: auth
change: add-user-authentication
status: active
relative_path: openspec/changes/add-user-authentication/specs/auth/spec.md
```

---

## Repository Discovery Rules

The adapter recognizes an OpenSpec repository if:

```
openspec/
    specs/
```

exists.

Optional directories:

```
changes/
changes/archive/
```

may be absent.

---

## Document Identification

Document identifiers SHOULD be deterministic.

Recommended format:

```
openspec:<artifact>:<relative-path>
```

Examples:

```
openspec:specification:specs/auth/spec.md

openspec:proposal:changes/add-user-authentication/proposal.md

openspec:tasks:changes/add-user-authentication/tasks.md

openspec:specification:changes/add-user-authentication/specs/api/spec.md
```

This guarantees stable identifiers across repeated scans while remaining compatible with the canonical `Document.id` contract defined in **F03**.
