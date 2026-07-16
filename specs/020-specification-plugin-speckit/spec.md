# Feature Specification: Specification Plugin — SpecKit

**Feature Branch**: `020-specification-plugin-speckit`

**Created**: 2026-07-16

**Status**: Draft

**Input**: User description: "SpecKit Specification Adapter Plugin"

---

# Overview

The SpecKit Specification Plugin implements the **Specification Adapter Plugin Interface (F03)** for repositories following the SpecKit project layout.

Its responsibility is limited to:

- detecting SpecKit repositories;
- discovering governance and feature specification artifacts;
- normalizing them into the canonical `Document` model;
- preserving repository structure and metadata for downstream semantic processing.

The adapter **does not execute SpecKit commands**, interpret requirements, validate architectural decisions, or infer relationships between artifacts. Those responsibilities belong to later stages of the semantic pipeline.

Unlike OpenSpec, SpecKit organizes specifications around **feature workspaces**, where each feature contains its complete lifecycle (specification, architecture, planning and implementation tasks).

---

# User Scenarios & Testing

## User Story 1 — Discover governance documents (Priority: P1)

A repository contains the SpecKit governance directory.

The adapter discovers all persistent governance artifacts.

**Why this priority**

Governance documents define global project constraints and provide context for downstream semantic analysis.

**Independent Test**

Create a repository containing `.specify/memory/constitution.md` and verify it is discovered as a canonical document.

### Acceptance Scenarios

1. **Given** a SpecKit repository

   **When** the adapter scans `.specify/memory`

   **Then** every governance document is discovered.

2. **Given** a repository without `.specify/memory`

   **When** scanning

   **Then** no governance documents are returned.

---

## User Story 2 — Discover feature workspaces (Priority: P1)

A repository contains multiple SpecKit feature directories.

The adapter discovers every feature artifact.

**Why this priority**

Each feature workspace represents a complete specification lifecycle.

**Independent Test**

Create multiple feature directories and verify every artifact is normalized.

### Acceptance Scenarios

1. **Given** multiple feature directories

   **When** scanning

   **Then** every feature is discovered.

2. **Given** a feature containing spec, plan and tasks

   **When** normalized

   **Then** every file becomes an independent Document.

3. **Given** optional artifacts

   **When** scanning

   **Then** they are discovered when present.

---

## User Story 3 — Preserve feature metadata (Priority: P1)

The adapter exposes repository structure without semantic interpretation.

**Why this priority**

Semantic extraction requires traceability back to the original SpecKit workspace.

**Independent Test**

Verify every normalized document contains feature metadata.

### Acceptance Scenarios

1. **Given** a specification document

   **When** normalized

   **Then** metadata contains the feature identifier.

2. **Given** an architecture document

   **When** normalized

   **Then** metadata identifies it as planning material.

3. **Given** a governance document

   **When** normalized

   **Then** metadata identifies it as global governance.

---

## User Story 4 — Detect SpecKit repositories (Priority: P1)

The Plugin Registry evaluates installed adapters.

The SpecKit adapter determines whether the repository follows the SpecKit convention.

**Why this priority**

Automatic adapter selection depends on reliable repository identification.

**Independent Test**

Verify `supports()` correctly identifies SpecKit repositories.

### Acceptance Scenarios

1. **Given** a SpecKit repository

   **When** `supports()` executes

   **Then** True is returned.

2. **Given** a repository using another SDD framework

   **When** `supports()` executes

   **Then** False is returned.

---

# Edge Cases

- Missing `.specify/`
- Missing `.specify/memory`
- Missing `constitution.md`
- Empty `specs/`
- Feature containing only `spec.md`
- Missing optional artifacts
- Invalid Markdown
- Duplicate feature identifiers
- Corrupted UTF-8 files
- Symbolic links
- Very large repositories
- Additional custom Markdown documents inside feature folders

---

# Constitution Check

## Engaged Principles

- Specification First
- Canonical Representation
- Plugin-Oriented Architecture
- Traceability
- Deterministic Processing

## Compliance Notes

The adapter preserves repository structure but never performs semantic interpretation.

All Markdown remains available for downstream semantic extraction.

---

# Requirements

## Functional Requirements

### Repository Detection

**FR-001**

The adapter MUST detect SpecKit repositories using one or more of the following markers:

- `.specify/`
- `.specify/memory/constitution.md`
- `specs/`

---

**FR-002**

The adapter MUST implement

```python
supports(repository_path)
```

without performing a full repository scan.

---

### Repository Scan

**FR-003**

The adapter MUST discover governance artifacts inside

```
.specify/memory/
```

---

**FR-004**

The adapter MUST recursively discover feature workspaces inside

```
specs/
```

---

**FR-005**

Every Markdown artifact MUST become one canonical Document.

Supported artifacts include:

| Artifact         | Document Type |
| ---------------- | ------------- |
| constitution.md  | constitution  |
| spec.md          | specification |
| plan.md          | plan          |
| tasks.md         | tasks         |
| research.md      | research      |
| data-model.md    | data-model    |
| checklists/\*.md | checklist     |

---

**FR-006**

The adapter MUST ignore framework helper scripts and executable assets located under `.specify/`, except documents intended for semantic consumption.

---

**FR-007**

Unknown Markdown files SHALL also be discovered and normalized using the canonical document type `unknown`.

---

### Normalization

**FR-008**

Every discovered artifact MUST be normalized into the canonical `Document` model defined by F03.

---

**FR-009**

The adapter MUST preserve raw Markdown without modification.

---

**FR-010**

The adapter MUST preserve document section hierarchy using `DocumentSection`.

---

**FR-011**

The adapter MUST NOT interpret:

- User Stories
- Requirements
- Acceptance Criteria
- Technical Decisions
- Tasks
- Checklists
- Parallel task markers (`[P]`)
- Research conclusions

These remain raw content.

---

### Metadata

**FR-012**

Every normalized document MUST contain the following metadata:

```yaml
framework: speckit
artifact_type:
feature:
workspace:
relative_path:
```

---

**FR-013**

Governance documents MUST include

```yaml
kind: governance
```

---

**FR-014**

Feature specifications MUST include

```yaml
kind: specification
```

---

**FR-015**

Planning documents MUST include

```yaml
kind: architecture
```

---

**FR-016**

Implementation task documents MUST include

```yaml
kind: implementation
```

---

**FR-017**

Research documents MUST include

```yaml
kind: research
```

---

**FR-018**

Checklist documents MUST include

```yaml
kind: checklist
```

---

### Plugin Registration

**FR-019**

The plugin MUST register through the Specification Adapter Plugin Interface defined by F03.

---

**FR-020**

Plugin metadata SHALL expose:

- plugin id
- plugin version
- supported framework
- supported artifact types

---

### Error Handling

**FR-021**

Individual file failures SHALL generate document-level errors.

---

**FR-022**

Malformed Markdown SHALL NOT interrupt repository scanning.

---

**FR-023**

Scanning SHALL continue after individual document failures.

---

# Key Entities

## SpecKit Repository

A repository organized according to the SpecKit conventions.

---

## Governance Document

Persistent documentation located under

```
.specify/memory/
```

that applies to the entire repository.

---

## Feature Workspace

A directory located under

```
specs/
```

representing one independent feature under development.

---

## Specification Artifact

Any Markdown document contributing to one feature lifecycle.

Possible artifact kinds include:

- specification
- architecture
- implementation
- research
- data-model
- checklist

---

# Success Criteria

**SC-001**

Repositories containing 500+ Markdown artifacts are scanned in under 5 seconds.

---

**SC-002**

100% of valid SpecKit artifacts are normalized.

---

**SC-003**

Malformed documents do not interrupt repository scanning.

---

**SC-004**

Governance documents and feature workspaces are correctly distinguished.

---

**SC-005**

Every normalized document is directly consumable by the Semantic Extraction Engine without requiring SpecKit-specific logic.

---

# Assumptions

- SpecKit repositories follow the published directory convention.
- Markdown files are UTF-8 encoded.
- Optional planning artifacts may be absent.
- Repository checkout has already occurred.
- Semantic interpretation is outside the adapter scope.
- The adapter is stateless.

---

# Data Model

## SpecKitAdapter

Implements the `SpecificationAdapter` protocol defined by F03.

```
SpecKitAdapter
    ├── supports(path)
    ├── scan(path)
    ├── scan_memory()
    ├── scan_features()
    ├── normalize_document()
    └── build_metadata()
```

---

## Metadata Mapping

| SpecKit Artifact | Canonical document_type | Metadata.kind  |
| ---------------- | ----------------------- | -------------- |
| constitution.md  | constitution            | governance     |
| spec.md          | specification           | specification  |
| plan.md          | plan                    | architecture   |
| tasks.md         | tasks                   | implementation |
| research.md      | research                | research       |
| data-model.md    | data-model              | research       |
| checklists/\*.md | checklist               | checklist      |
| \*.md            | unknown                 | unknown        |

---

## Canonical Metadata Example

```yaml
framework: speckit
artifact_type: specification
kind: specification
feature: 001-add-user-authentication
workspace: specs/001-add-user-authentication
relative_path: specs/001-add-user-authentication/spec.md
```

Example for a governance document:

```yaml
framework: speckit
artifact_type: constitution
kind: governance
feature: null
workspace: .specify/memory
relative_path: .specify/memory/constitution.md
```

---

## Repository Discovery Rules

The adapter recognizes a SpecKit repository when at least one of the following conditions is satisfied:

```
.specify/
```

or

```
.specify/memory/constitution.md
```

or

```
specs/
```

exists.

The repository MAY omit optional planning artifacts.

---

## Document Identification

Document identifiers SHOULD be deterministic.

Recommended format:

```
speckit:<artifact>:<relative-path>
```

Examples:

```
speckit:constitution:.specify/memory/constitution.md

speckit:specification:specs/001-add-user-authentication/spec.md

speckit:plan:specs/001-add-user-authentication/plan.md

speckit:tasks:specs/001-add-user-authentication/tasks.md

speckit:checklist:specs/001-add-user-authentication/checklists/requirements.md
```

This identification strategy guarantees stable document identities across repeated scans while remaining fully compatible with the canonical `Document` contract defined by **F03**.
