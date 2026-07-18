# Implementation Plan: Specialized Deterministic Fallbacks

**Branch**: `029-deterministic-fallback-specialists` | **Date**: 2026-07-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/029-deterministic-fallback-specialists/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Create framework-specific deterministic rule packs (`speckit_rules.yaml`, `openspec_rules.yaml`) with rich regex patterns that extract full CFM and CSM semantic models from SpecKit and OpenSpec repositories, replacing the current minimal heading-based rules. All extraction is purely deterministic — no LLM involved. The OpenSpec examples in `tests/openspec/` (29 domains, 41 changes) and specmetrics itself (29 features) serve as validation corpora with a ≤30s end-to-end latency target.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: markdown-it-py (Markdown parsing), ruamel.yaml (rule pack YAML), networkx (evidence graph), pydantic v2 (canonical models) — all existing in the codebase; no new dependencies introduced.

**Storage**: N/A — rule packs are YAML files shipped with the codebase; no runtime persistent storage needed.

**Testing**: pytest, ruff

**Target Platform**: Linux, macOS, Windows

**Project Type**: CLI tool (specmetrics) — rule packs are data files, not code

**Performance Goals**: OpenSpec examples in `tests/openspec/` (29 domain specs + 41 change artifacts) processed end-to-end in ≤ 30s

**Constraints**: Specialist rule packs MUST be additive-only (never override default rules); MUST NOT require changes to the deterministic engine or CFM/CSM classifiers; individual rule failures MUST NOT abort the full extraction run.

**Scale/Scope**: 29 SpecKit feature workspaces + 29 OpenSpec domain specs + 41 OpenSpec change artifacts across 3 active + 38 archived changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: I (Specification First), III (Semantic Before Structural), IV (LLM-Assisted, Deterministic Results), V (Evidence First), VII (Canonical Representation), IX (Rule Externalization), XIV (Layer Independence)

**Compliance Verifications**:
- [x] Specification First: Specialist fallbacks consume normalized Document objects from the Specification Adapter — specifications are the primary source.
- [x] Evidence First: Every extracted element preserves EvidenceReference (document ID, section, text fragment, rule ID) via the existing model.
- [x] Canonical Representation: Specialist fallbacks produce ExtractedElement objects in the canonical model; downstream CFM/CSM builders consume these without knowing the extraction source.
- [x] Plugin-Oriented: Rule packs are external YAML files loaded by the existing rule engine — no core code changes needed; frameworks are supported through data, not plugin code.
- [x] Rule Externalization: Specialist rules are organized as external YAML rule packs (`speckit_rules.yaml`, `openspec_rules.yaml`), versioned via semver metadata field.
- [x] Layer Independence: Specialist fallbacks implement the `SemanticExtractionEngine` interface; the pipeline only invokes this interface, never the rule pack internals.
- [x] Open by Default: Rule pack YAML schema is documented in `contracts/rule-pack-contract.md`; patterns are derived from real file analysis of 29+ repositories.

**Gate result**: PASS — All engaged principles verified. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/029-deterministic-fallback-specialists/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── rule-pack-contract.md
├── checklists/
│   └── requirements.md  # Pre-existing quality checklist
└── spec.md              # Feature specification
```

### Source Code (repository root)

```text
specmetrics/
├── kernel/
│   └── rules/                   # Rule pack directory
│       ├── speckit_rules.yaml   # NEW: Speckit specialist rule pack
│       ├── openspec_rules.yaml  # NEW: OpenSpec specialist rule pack
│       └── default_rule_pack.yaml
├── tests/
│   ├── fixtures/
│   │   ├── speckit/             # NEW: SpecKit test fixtures
│   │   └── openspec/            # NEW: OpenSpec test fixtures (FlowSource subset from tests/openspec/)
│   └── unit/
│       └── kernel/
│           └── rules/           # NEW: Rule pack unit tests
```

**Structure Decision**: Single-project layout (Option 1). The rule packs are data files under the existing `kernel/rules/` directory. Test fixtures mirror the real repository structures for e2e validation.

## Complexity Tracking

> No Constitution Check violations to justify.
