# Implementation Plan: Specification Plugin — OpenSpec

**Branch**: `019-specification-plugin-openspec` | **Date**: 2026-07-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/019-specification-plugin-openspec/spec.md`

## Summary

Implement an OpenSpec Specification Adapter plugin that discovers, normalizes, and exposes specification artifacts from repositories following the OpenSpec convention. The adapter detects OpenSpec repositories via filesystem markers (`openspec/specs/`), discovers current specifications and active/archived change proposals, normalizes every Markdown artifact into the canonical `Document` model with preserved structural metadata, and supports error isolation for malformed or unreadable files.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**:
- `pathlib` — for filesystem traversal (stdlib, no additional dependency)
- `structlog` — for structured logging (platform standard)

**Storage**: N/A (stateless adapter; documents passed to pipeline in-memory)

**Testing**: pytest (platform standard)

**Target Platform**: Linux desktop/server (local CLI execution)

**Project Type**: Library/Plugin within the SpecMetrics platform (`specmetrics/plugins/adapter/`)

**Performance Goals**: Scan 500 Markdown artifacts in under 5 seconds (SC-001); >1000 artifacts is an advisory stress test only

**Constraints**:
- Must detect repositories without full scan (FR-002) — check for `openspec/` + `openspec/specs/` path existence
- Must NOT interpret requirements, scenarios, or change markers (FR-011)
- Must preserve raw Markdown (FR-009) and section hierarchy (FR-010)
- Must handle missing optional directories (`changes/`, `changes/archive/`) gracefully
- Stateless — each scan is independent with no cached state
- Temp folder exclusion: `.git`, `__pycache__`, `.venv`, `node_modules`, `.specify`, `_`-prefixed folders

**Scale/Scope**: Single framework adapter (OpenSpec only); complements SpecKit adapter

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: Specification First, Canonical Representation, Plugin-Oriented Architecture, Traceability, Deterministic Processing

**Compliance Verifications**:
- [x] Specification First: The adapter discovers specification artifacts without modifying or interpreting them. Every document becomes available for downstream semantic extraction unchanged.
- [x] Canonical Representation: All artifacts are normalized into the canonical `Document` model (F03). The adapter never leaks OpenSpec-specific structures into pipeline stages.
- [x] Plugin-Oriented: The adapter registers via the Specification Adapter Entry Point (F03) and is discovered by the Plugin Registry at startup.
- [x] Traceability: Metadata preserves the original repository path, domain, change identifier, and artifact type — enabling full traceability to source documents.
- [x] Deterministic Processing: Given the same filesystem state, the adapter produces identical document lists. No heuristics or probabilistic decisions.

## Project Structure

### Documentation (this feature)

```text
specs/019-specification-plugin-openspec/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Adapter design decisions
├── data-model.md        # Entity definitions and metadata mappings
├── quickstart.md        # Validation guide
└── contracts/
    └── adapter-interface.md
```

### Source Code (repository root)

```text
specmetrics/
└── plugins/
    └── adapter/
        └── openspec/
            ├── __init__.py
            ├── plugin.py          # Plugin entry point + OpenSpecAdapter class
            ├── scanner.py         # Filesystem discovery and artifact scanning
            ├── normalizer.py      # Document normalization and section parsing
            └── metadata.py        # Metadata builder and kind resolution

tests/
├── unit/
│   └── adapter/
│       └── openspec/
│           ├── test_scanner.py
│           ├── test_normalizer.py
│           ├── test_metadata.py
│           └── test_plugin.py
└── integration/
    └── adapter/
        └── openspec/
            └── test_full_scan.py
```

**Structure Decision**: Single adapter under `specmetrics/plugins/adapter/openspec/`, following the existing plugin pattern. The adapter implements the `SpecificationAdapter` Protocol from F03.

## Complexity Tracking

No constitution violations detected. All engaged principles are satisfied by the design decisions documented above.
