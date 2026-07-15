# Implementation Plan: Specification Adapter Plugin Interface

**Branch**: `004-specification-adapter-interface` | **Date**: 2026-07-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-specification-adapter-interface/spec.md`

## Summary

Define and implement the Specification Adapter plugin interface that SDD
framework adapters must implement. Each adapter discovers specification
documents in a repository, reads them, and normalizes them into a
framework-agnostic `Document` representation. Adapters are packaged as
SpecMetrics plugins (F02 contract) and never perform semantic interpretation.

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: `pathlib` (stdlib), `structlog` (existing),
F02 PluginRegistry (existing), pytest (testing)

**Storage**: N/A — adapter reads from local filesystem, no persistence

**Testing**: pytest (unit for adapter interface compliance; integration for
F02 plugin lifecycle)

**Target Platform**: Linux

**Project Type**: library (kernel module: adapter interface + adapter registry)

**Performance Goals**: Full repository scan of 100+ documents within 5 seconds
(SC-001); single document read within 50ms

**Constraints**: Adapters are stateless; each scan() call is independent;
documents are text-based (Markdown, YAML); no semantic interpretation in the
adapter layer

**Scale/Scope**: Adapters handle local filesystem repositories; remote
repositories are checked out before the adapter runs; supports multiple
simultaneously installed adapters

## Constitution Check

*GATE: Phase 1 design complete. Post-design re-check passed.*

**Engaged Principles**: I (Specification First), VII (Canonical Representation),
VIII (Plugin-Oriented), XIV (Layer Independence)

**Compliance Verifications**:
- [x] Specification First: Adapters exist solely to make specifications
  accessible. The output (Document objects) feeds directly into the pipeline
  that measures specifications as engineering assets.
- [x] Canonical Representation: The adapter interface produces a
  framework-agnostic Document. No downstream component depends on any SDD
  framework format.
- [x] Plugin-Oriented: Each adapter is a plugin discovered through F02. New
  framework support is added by installing a new adapter plugin — never by
  modifying the core.
- [x] Layer Independence: The adapter interface is defined as a stable
  contract (Protocol). The kernel, semantic extraction, and measurement layers
  depend only on this contract, never on adapter implementations.

**Research Resolution**:
- Interface design: Protocol class (structural subtyping), matching F01
  EventHandler pattern
- Document types: Advisory string labels, not strict enum — allows forward
  compatibility
- Metadata schema: Free-form `dict[str, Any]` preserving framework-specific
  info
- F02 integration: AdapterRegistry wraps PluginRegistry.get_by_type("adapter")
- Error isolation: Per-document try/except within scan()

**Gate result**: PASS — all principles satisfied.

## Project Structure

### Documentation (this feature)

```text
specs/004-specification-adapter-interface/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── adapter-interface.md
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
specmetrics/
├── kernel/
│   ├── __init__.py
│   ├── adapter_interface.py      # NEW — SpecificationAdapter Protocol, Document model
│   ├── adapter_registry.py       # NEW — registry for adapters via F02 PluginRegistry
│   └── ... (existing F01 + F02 files)
└── tests/
    ├── unit/
    │   ├── test_adapter_interface.py  # NEW
    │   └── test_adapter_registry.py   # NEW
    └── integration/
        └── test_adapter_pipeline.py   # NEW
```

**Structure Decision**: The adapter interface lives in `specmetrics/kernel/`
because it is a core contract consumed by the Pipeline Engine. It depends on
F02 (PluginRegistry) but not on any specific adapter implementation.

## Complexity Tracking

No constitution violations expected. The adapter interface is a straightforward
Protocol class plus a Document data model. The main complexity is ensuring the
interface is general enough to support multiple SDD frameworks without leaking
framework-specific concepts into the contract.
