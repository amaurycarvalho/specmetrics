# Implementation Plan: OpenSpec Operation Extraction Rules

**Branch**: `035-openspec-operation-rules` | **Date**: 2026-07-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/035-openspec-operation-rules/spec.md`

## Summary

Repurpose 9 existing OpenSpec extraction rules from `type: "fact"` to `type: "operation"` in `openspec_rules.yaml`. This is a YAML-only change — no engine, builder, or classifier code is modified. The deterministic engine and CFM builder already support `type: "operation"`; the rules simply weren't using it for clearly behavioral content (THEN assertions, AND clauses, SHALL/DEVE statements, requirement headings, task items, decision records).

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: None new — only YAML rule file changes

**Storage**: `specmetrics/kernel/rules/openspec_rules.yaml` (single file modified)

**Testing**: pytest (existing test suite validates rule loading and extraction)

**Target Platform**: Linux/macOS/Windows CLI tool

**Project Type**: CLI + library

**Performance Goals**: No measurable impact — rule type change doesn't affect matching performance

**Constraints**: Zero code changes. Only YAML `type` field values change from `"fact"` to `"operation"`.

**Scale/Scope**: 9 rule entries in a single YAML file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**:
- III. Semantic Before Structural: THEN clauses are operations, not generic facts. This is a semantic correction.
- IV. LLM-Assisted, Deterministic Results: Rules apply to the deterministic fallback engine.
- V. Evidence First: No new element types — evidence references preserved.
- IX. Rule Externalization: Changes are in external YAML, not hardcoded.

**Compliance Verifications**:
- [x] Specification First: Primary input is software specifications (OpenSpec format)
- [x] Evidence First: Existing evidence references preserved unchanged
- [x] Canonical Representation: Operations flow through CFM to all measurement engines
- [x] Plugin-Oriented: YAML rule packs are the standard plugin mechanism for extraction rules
- [x] Rule Externalization: Rules are in `openspec_rules.yaml`, overridable per project
- [x] Layer Independence: Extraction layer → CFM layer unchanged
- [x] Open by Default: YAML rule format is documented and human-readable

## Project Structure

### Documentation (this feature)

```text
specs/035-openspec-operation-rules/
├── spec.md
├── plan.md              # This file
├── research.md          # Phase 0: rule analysis and mapping
├── data-model.md        # Phase 1: entity changes (none)
├── quickstart.md        # Phase 1: validation guide
└── tasks.md             # Phase 2 (/speckit.tasks)
```

### Source Code (repository root)

```text
specmetrics/kernel/rules/
└── openspec_rules.yaml    # MODIFIED: 9 rule type changes (fact → operation)
```

**Structure Decision**: Single file change. No new files, no new directories, no code changes.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.
