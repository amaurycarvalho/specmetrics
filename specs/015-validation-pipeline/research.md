# Research: Validation Pipeline

## Overview

Research findings and technology decisions for the Validation Pipeline feature.

## Decisions

### Decision: markdown-it-py for spec parsing

**Rationale**: Already used in the Semantic Extraction layer for parsing markdown specs. Reusing avoids adding a new dependency and ensures consistent document representation across pipeline stages. Provides AST-level access to document structure (headings, sections, content), which is exactly what structural validation needs.

**Alternatives considered**:
- Raw regex parsing — fragile, breaks with formatting variations
- mistune — lighter but lacks maintained AST API for structural queries
- pypandoc — heavy dependency, not already in the project

### Decision: Pydantic v2 for validation rule models

**Rationale**: Already the project's standard for data modeling. Provides schema validation, serialization, and self-documenting models. ValidationRule and ValidationResult entities benefit from Pydantic's built-in validation guarantees.

**Alternatives considered**:
- dataclasses — no validation, no serialization
- attrs — validation requires additional libraries
- Manual dicts — no type safety, no documentation

### Decision: Plugin-based validation rule loading

**Rationale**: FR-009 requires externalizable rules. Using the project's existing plugin discovery mechanism (Python Entry Points) allows validation rules to be contributed by the same plugin system used by adapters, semantic providers, and exporters. No new plugin infrastructure needed.

**Alternatives considered**:
- Hardcoded rule registry — violates Rule Externalization (IX)
- Configuration-file-only rules — less extensible for third-party contributions

### Decision: Validation as independent kernel module

**Rationale**: FR-001 through FR-010 describe a self-contained validation capability that must not depend on measurement engine internals (Layer Independence XIV). Placing it in `kernel/validation/` as a standalone module enforces this separation.

**Alternatives considered**:
- Adding validation to the measurement engine — violates Layer Independence, creates coupling
- Validation as a CLI-only feature — limits reuse by other pipeline stages

### Decision: `specmetrics validate` CLI subcommand

**Rationale**: Aligns with existing CLI architecture (Typer-based, command-per-feature). Single-spec, batch, and constitutional checks are sub-options of the same command.

**Alternatives considered**:
- Separate `specmetrics-validate` binary — unnecessary process overhead
- Hidden behind a flag on `specmetrics measure` — conflates two pipeline stages

## Dependencies

### Existing (reuse)

| Dependency | Usage |
|---|---|
| markdown-it-py | Parse spec markdown into AST for structural checks |
| Pydantic v2 | ValidationRule, ValidationResult, ValidationReport models |
| structlog | Structured validation output (pass/fail per rule, summary) |
| Typer | CLI command integration |
| pluggy / entry points | Plugin-based rule discovery |

### New (if any)

No new external dependencies required. Validation-specific logic is all custom.

## Integration Points

| Interface | Direction | Purpose |
|---|---|---|
| CLI (`specmetrics validate`) | User → System | Accept spec path(s), report results |
| Plugin discovery (entry points) | System → Plugins | Load external ValidationRule implementations |
| stdout/stderr (structured logs) | System → User | Pass/fail report, actionable error messages |
| Exit codes | System → Shell | Non-zero on validation failure (CI/CD integration) |
