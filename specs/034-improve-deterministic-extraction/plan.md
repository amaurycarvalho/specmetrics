# Implementation Plan: Improve Deterministic Extraction Engine

**Branch**: `034-improve-deterministic-extraction` | **Date**: 2026-07-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/034-improve-deterministic-extraction/spec.md`

## Summary

Enhance the deterministic semantic extraction engine to identify operations, infer SNAP semantic markers, and correctly classify actors — enabling all eight measurement metrics (FPA, SFP, SNAP, Story Points, BCP, TShirt, Token Points, Cognitive Points) to produce non-zero results when running without an LLM. The primary gap is the absence of `type: "operation"` rules in the rule packs, which prevents functional process construction and cascades to five zero-output metrics.

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: pydantic, structlog, ruamel.yaml, markdown-it-py, networkx (all already in use)

**Storage**: YAML rule packs (`.yaml` files in `specmetrics/kernel/rules/`), JSONL evidence graph, JSON run artifacts

**Testing**: pytest (existing test suite at `specmetrics/tests/`)

**Target Platform**: Linux/macOS/Windows CLI tool (Python package)

**Project Type**: CLI + library

**Performance Goals**: Extraction should not degrade measurably. Current deterministic extraction processes ~260 documents / ~2000 graph nodes in ~8s. Adding operation rules may increase extraction time by <10%. Target: no regression in overall pipeline duration.

**Constraints**: Must work without LLM (deterministic fallback). No external API calls in extraction path. New rules must follow existing `default_rule_pack.yaml` and `speckit_rules.yaml` structure.

**Scale/Scope**: Current project has ~260 documents producing ~2000 evidence graph nodes. Feature must handle this volume without issues.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**:
- III. Semantic Before Structural: Classifier improvements prioritize meaning over document format
- IV. LLM-Assisted, Deterministic Results: All changes apply to the deterministic fallback engine
- V. Evidence First: New element types maintain evidence references
- VII. Canonical Representation: Improvements operate on the CFM, not framework-specific artifacts
- IX. Rule Externalization: Operation rules are in external YAML files, not hardcoded

**Compliance Verifications**:
- [x] Specification First: Primary input is software specifications (SpecKit format)
- [x] Evidence First: All new elements preserve graph_node_id, document_id, section_id, text evidence
- [x] Canonical Representation: Operations/actors flow through CFM, not framework-specific structures
- [x] Plugin-Oriented: Rule packs are already plugin-structured; classifier changes extend existing functions
- [x] Rule Externalization: Operation extraction rules are YAML files, overridable per project
- [x] Layer Independence: Extraction layer → CFM layer → Measurement layer — each with stable contracts
- [x] Open by Default: YAML rule format is documented and human-readable

## Project Structure

### Documentation (this feature)

```text
specs/034-improve-deterministic-extraction/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0: rule pattern design, marker mapping, actor heuristics
├── data-model.md        # Phase 1: entity changes
├── quickstart.md        # Phase 1: validation guide
├── contracts/           # Phase 1: not applicable (no external interfaces)
└── tasks.md             # Phase 2 (created by /speckit.tasks)
```

### Source Code (repository root)

```text
specmetrics/
├── kernel/
│   ├── rules/
│   │   ├── default_rule_pack.yaml      # MODIFIED: add operation rules
│   │   ├── speckit_rules.yaml          # MODIFIED: add operation rules, change existing GWT to operation type
│   │   └── openspec_rules.yaml         # UNCHANGED (OpenSpec deferred)
│   ├── cfm/
│   │   ├── builder.py                  # MODIFIED: add semantic_marker inference
│   │   └── classifier.py              # MODIFIED: improve _classify_entity actor detection
│   └── deterministic_engine.py         # UNCHANGED (already supports type:"operation")
├── plugins/
│   └── measurement/
│       └── snap/
│           └── assessor.py             # UNCHANGED (reads semantic_marker from metadata)
└── tests/
    ├── unit/
    │   └── test_cfm_classifier.py      # MODIFIED/EXTENDED: actor classification tests
    └── integration/
        └── test_deterministic_pipeline.py  # MODIFIED/EXTENDED: operation extraction tests
```

**Structure Decision**: Standard specmetrics project structure. Changes are confined to `kernel/rules/` (YAML rule packs) and `kernel/cfm/` (builder + classifier). No new directories or files needed. Tests extended in existing test files.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.
