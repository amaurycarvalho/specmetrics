# Implementation Plan: Rule Pack Engine

**Branch**: `010-rule-pack-engine` | **Date**: 2026-07-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/010-rule-pack-engine/spec.md`

## Summary

The Rule Pack Engine is a deterministic pipeline stage that loads external measurement policies from `.specify/rules/` and applies them to the Canonical Functional Model before the Measurement Engine runs. It supports exclusion rules, complexity threshold overrides, VAF configuration, and glossary overrides — all defined as declarative YAML files. The engine annotates every applied rule on the affected CFM elements, preserving full traceability for downstream explainability.

## Technical Context

**Language/Version**: Python >=3.12 (3.13 per constitution)

**Primary Dependencies**: pydantic v2 (models), ruamel.yaml (Rule Pack parsing), structlog (logging), networkx (CFM graph operations)

**Storage**: File system — Rule Packs are YAML files in `.specify/rules/`

**Testing**: pytest (unit + integration), with fixture Rule Packs and mock CFM inputs

**Target Platform**: Linux, macOS (CLI execution)

**Project Type**: CLI tool + MCP server (plugin-oriented architecture, event-driven pipeline)

**Performance Goals**: Rule Pack loading and validation < 2s for 10 rules + 5 overrides; application < 3s for CFM with 100+ functions

**Constraints**: Deterministic output (identical inputs → identical annotated CFM); no LLM or non-deterministic operations in rule application; must be a discoverable pipeline stage via handler registry; Rule Packs are declarative only (no scripting)

**Scale/Scope**: Single pipeline stage, single project directory; 1–20 Rule Pack files per project, each with 1–50 rules

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**:
- **IX (Rule Externalization)** — Direct implementation: all policies are external YAML files
- **VI (Explainability by Design)** — Every applied rule is annotated on affected CFM elements
- **VII (Canonical Representation)** — Operates exclusively on the CanonicalFunctionalModel
- **IV (LLM-Assisted, Deterministic Results)** — Pure deterministic rule application
- **XIV (Layer Independence)** — Depends only on CFM contract; no coupling to extraction or measurement layers
- **VIII (Plugin-Oriented)** — Stage is a discoverable plugin through the handler registry

**Compliance Verifications**:
- [x] Specification First: Is the primary input a software specification? — No, it consumes the CanonicalFunctionalModel, not raw specs; compliant by architecture layering
- [x] Evidence First: Does the design preserve traceability to evidence? — Every applied rule references the originating Rule Pack file and rule; annotations link back to source evidence via CFM elements
- [x] Canonical Representation: Does the feature operate on the CFM rather than framework-specific artifacts? — Yes, CFM is the sole input and output
- [x] Plugin-Oriented: Is the capability implemented as a plugin when it could be external? — Yes, the engine is a handler registered via the HandlerRegistry
- [x] Rule Externalization: Are organizational policies externalized as Rule Packs? — Yes, this is the core purpose
- [x] Layer Independence: Does the component depend only on stable abstractions of adjacent layers? — Depends only on CFM contract and HandlerRegistry/EventBus; no coupling to adapter, extraction, or measurement layers
- [x] Open by Default: Are interfaces documented and standards-based? — Rule Pack format is documented YAML; pipeline stage contract follows the established EventHandler protocol

## Project Structure

### Documentation (this feature)

```text
specs/010-rule-pack-engine/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Created by /speckit.tasks
```

### Source Code (repository root)

```text
specmetrics/
├── kernel/
│   └── cfm/
│       └── model.py              # CanonicalFunctionalModel (existing)
├── plugins/
│   ├── measurement/
│   │   └── apf/
│   │       ├── models.py         # Existing RulePack model → to be extracted/shared
│   │       └── rule_applicator.py # Existing → to be refactored as consumer of engine output
│   └── rule_pack/                 # NEW: Rule Pack Engine plugin
│       ├── __init__.py
│       ├── plugin.py             # EventHandler implementation
│       ├── loader.py             # Rule Pack file discovery and parsing
│       ├── validator.py          # Rule Pack schema validation
│       ├── applicator.py         # Core rule application logic
│       ├── annotator.py          # CFM annotation with applied rules
│       └── models.py             # RulePack schema (extracted from measurement plugin)
└── tests/
    └── plugins/
        └── rule_pack/            # NEW: Rule Pack Engine tests
            ├── test_loader.py
            ├── test_validator.py
            ├── test_applicator.py
            └── test_plugin.py
```

**Structure Decision**: The Rule Pack Engine is a new plugin under `specmetrics/plugins/rule_pack/`, following the same pattern as the existing measurement plugin. The `RulePack` model is extracted from the measurement plugin to a shared location to avoid circular dependencies.

## Complexity Tracking

No constitution violations to justify.

