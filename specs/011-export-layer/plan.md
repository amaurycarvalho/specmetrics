# Implementation Plan: Export Layer

**Branch**: `011-export-layer` | **Date**: 2026-07-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/011-export-layer/spec.md`

## Summary

Implement the Publication Layer for SpecMetrics: expose functional measurement results via exporters (JSON, CSV, XML) and publishers (OpenTelemetry). Exporters and publishers are implemented as plugins discovered through the existing plugin registry. The layer consumes data exclusively from the Canonical Functional Model and preserves full evidence traceability.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: Pydantic v2 (models/schemas), structlog (logging), OpenTelemetry SDK API (telemetry publishing), NetworkX (CFM data structures already in kernel)

**Storage**: N/A — export layer produces files and network telemetry; no persistent storage.

**Testing**: pytest with plugin test fixtures (mocked CFM, mock telemetry receiver)

**Target Platform**: Linux (local execution via CLI and MCP Server per constitution deployment model)

**Project Type**: Python library with CLI interface (Typer)

**Performance Goals**: <5s total for 3-format export of 1,000 functions (SC-001); <60s for 10,000 functions (SC-005); export overhead should not add >10% to measurement pipeline time

**Constraints**: Serial per-format export; overwrite existing files with warning; OS-level file permissions for access control; >10% overhead triggers warning

**Scale/Scope**: 1,000–10,000 functions per measurement run; single-user local execution for v1

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: V (Evidence First), VI (Explainability by Design), VII (Canonical Representation), VIII (Plugin-Oriented Architecture), XI (Observability as a Native Capability)

**Compliance Verifications**:
- [x] Specification First: Export layer consumes the Canonical Functional Model, whose content is derived from software specifications. Measurements exported originate from specification-driven analysis.
- [x] Evidence First: FR-002 mandates evidence references in every export artifact, preserving traceability to source specification elements.
- [x] Canonical Representation: FR-005 requires exporters consume data exclusively from the CFM — no direct access to framework-specific artifacts.
- [x] Plugin-Oriented: FR-007/FR-008 define export/publisher plugins discovered via the plugin registry. Core platform defines interfaces only. ✓
- [x] Rule Externalization: N/A — Rule Packs govern measurement methodology, not export formatting. Export formatting decisions are presentation-layer concerns.
- [x] Layer Independence: Exporters depend only on CFM contracts (stable abstraction). Publishers depend only on exporter contracts. No layer below the kernel is accessed.
- [x] Open by Default: All export formats are open standards (JSON, CSV, XML). Publisher uses OpenTelemetry standard. Plugin interfaces are documented.

## Project Structure

### Documentation (this feature)

```text
specs/011-export-layer/
├── spec.md               # Feature specification (/speckit.specify command output)
├── plan.md               # This file (/speckit.plan command output)
├── research.md           # Phase 0 output (/speckit.plan command)
├── data-model.md         # Phase 1 output (/speckit.plan command)
├── quickstart.md         # Phase 1 output (/speckit.plan command)
├── contracts/            # Phase 1 output (/speckit.plan command)
│   ├── exporter-plugin.md
│   └── publisher-plugin.md
├── checklists/
│   └── requirements.md   # Spec quality checklist
└── tasks.md              # Phase 2 output (/speckit.tasks command — NOT created here)
```

### Source Code (repository root)

```text
specmetrics/
├── plugins/
│   ├── exporter/              # Built-in exporters (JSON, CSV, XML)
│   │   ├── __init__.py
│   │   ├── base.py            # Abstract base exporter plugin
│   │   ├── json_exporter.py
│   │   ├── csv_exporter.py
│   │   └── xml_exporter.py
│   └── publisher/             # Built-in publishers (OpenTelemetry)
│       ├── __init__.py
│       ├── base.py            # Abstract base publisher plugin
│       └── otel_publisher.py
├── kernel/
│   ├── canonical_model.py     # CFM types (existing; may need export view)
│   └── registry.py            # Plugin registry (existing; extended for export types)
├── cli/
│   └── export_commands.py     # CLI commands for export/publish (new)
└── mcp/
    └── tools/
        └── export_tools.py    # MCP tool definitions for export (new)

tests/
├── plugins/
│   ├── exporter/
│   │   └── test_exporters.py
│   └── publisher/
│       └── test_publishers.py
└── integration/
    └── test_export_pipeline.py
```

**Structure Decision**: Single Python project with plugin sub-packages following the existing `specmetrics/plugins/` convention. New directories `exporter/` and `publisher/` added under `plugins/`. CLI and MCP integration files added to existing `cli/` and `mcp/` directories.

## Complexity Tracking

No constitution violations to justify.
