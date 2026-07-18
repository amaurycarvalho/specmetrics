# Feature Specification: Specialized Deterministic Fallbacks

**Feature Branch**: `029-deterministic-fallback-specialists`

**Created**: 2026-07-18

**Status**: Draft

**Input**: User description: "Criar fallbacks deterministicos especializados com regex para speckit e openspec"

## Clarifications

### Session 2026-07-18

- **Q**: How should extraction rule match/miss behavior be surfaced for debugging and validation? → **A**: Structured debug output with match traces per rule and unmatched pattern statistics, integrated into the evidence pipeline.
- **Q**: What latency target should the deterministic pipeline meet? → **A**: OpenSpec examples in `tests/openspec/` (29 domain specs + 41 change artifacts) processed end-to-end within ≤ 30s.
- **Q**: What is explicitly out of scope for this feature? → **A**: LLM hybrid/assisted extraction mode — only purely deterministic extraction is in scope.
- **Q**: How should specialist rule packs be versioned for compatibility tracking? → **A**: Semantic versioning (`major.minor.patch`) embedded in rule pack YAML metadata.
- **Q**: What operational observability signals should the deterministic extraction emit beyond debug output? → **A**: Per-document extraction success rate ≥ 99% (rules executed vs rules failed), exposed as a counter metric.
- **Q**: Why was regex-based extraction chosen over AST/Markdown-parser-based extraction? → **A**: Regex offers lower implementation complexity, easier rule externalization (YAML), and sufficient precision for the structured Markdown patterns observed in Speckit/OpenSpec templates. AST parsing would be more precise but requires per-format parser maintenance and complicates rule customization.

## Speckit Format Analysis _(discovered from specmetrics specs/)_

The specmetrics project itself serves as the reference Speckit repository — 29 feature workspaces (`001` through `029`), ~200 markdown files across 8 document types. The patterns below are derived from concrete file analysis.

### Directory Structure

```
specs/
├── 001-mvp-release-outline/                  # Feature workspace (3-digit prefix + kebab name)
│   ├── spec.md                               # Required: feature specification
│   ├── plan.md                               # Optional: implementation plan
│   ├── tasks.md                              # Optional: implementation tasks
│   ├── research.md                           # Optional: research notes
│   ├── data-model.md                         # Optional: data model
│   ├── quickstart.md                         # Optional: validation/quickstart
│   ├── checklists/
│   │   └── requirements.md                   # Optional: quality checklists
│   └── contracts/                            # Optional: interface contracts
│       ├── canonical-model-contract.md
│       └── ...
├── 002-kernel-pipeline-engine/
│   └── ... (same structure)
└── ... (29 feature directories total)
```

Additional governance location:

```
.specify/
├── memory/
│   └── constitution.md                       # Governance: core principles
└── templates/
    ├── spec-template.md                      # Spec template
    ├── plan-template.md
    ├── tasks-template.md
    ├── checklist-template.md
    └── constitution-template.md
```

### Document Types, Their Sections and Regex Patterns

#### 1. `spec.md` — Feature Specification (required in every feature)

| Section                      | Regex Pattern                                                              | Example from Real Files                                                                                  |
| ---------------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Feature title                | `^# Feature Specification: (.+)$`                                          | `# Feature Specification: Canonical Functional Model Builder`                                            |
| Branch ID                    | `^\*\*Feature Branch\*\*: \`(\d{3}-[a-z0-9-]+)\`$`                         | `**Feature Branch**: \`007-canonical-functional-model\``                                                 |
| Created date                 | `^\*\*Created\*\*: (\d{4}-\d{2}-\d{2})$`                                   | `**Created**: 2026-07-15`                                                                                |
| Status                       | `^\*\*Status\*\*: (\w+)$`                                                  | `**Status**: Draft`                                                                                      |
| Clarifications               | `^## Clarifications$`                                                      | `## Clarifications`                                                                                      |
| Session                      | `^### Session \d{4}-\d{2}-\d{2}$`                                          | `### Session 2026-07-16`                                                                                 |
| Q&A line                     | `^-\s+\*\*Q\d+\*\*: (.+) → \*\*A\*\*: (.+)$`                               | `- **Q1**: ... → **A**: ...`                                                                             |
| Implementation note          | `^-\s+\*\*IMP-\d+\*\*: (.+)$`                                              | `- **IMP-1**: Added EmphasisVisitor...`                                                                  |
| User Scenarios               | `^## User Scenarios & Testing.*$`                                          | `## User Scenarios & Testing *(mandatory)*`                                                              |
| User Story header            | `^### User Story (\d+) [—–-] (.+) \(Priority: (P[1-3])\)$`                 | `### User Story 1 - Transform evidence graph... (Priority: P1)`                                          |
| User Story body              | Paragraph below `### User Story` heading                                   | Free text describing the user journey                                                                    |
| Priority justification       | `^\*\*Why this priority\*\*: (.+)$`                                        | `**Why this priority**: This is the core transformation...`                                              |
| Independent Test             | `^\*\*Independent Test\*\*: (.+)$`                                         | `**Independent Test**: Can be fully tested by providing...`                                              |
| Acceptance Scenario (inline) | `^(\d+)\. \*\*Given\*\* (.+), \*\*When\*\* (.+), \*\*Then\*\* (.+)$`       | `1. **Given** an evidence graph..., **When** the CFM Builder..., **Then** the resulting CFM contains...` |
| Acceptance Scenario (GWT)    | `^-\s+\*\*Given\*\* (.+)$` / `^\*\*When\*\* (.+)$` / `^\*\*Then\*\* (.+)$` | `- **Given** a valid specification repository`                                                           |
| Edge Cases header            | `^### Edge Cases$`                                                         | `### Edge Cases`                                                                                         |
| Edge Case item               | `^-\s+What happens (.+)\? (.+)$`                                           | `- What happens when the evidence graph is empty? The CFM Builder produces...`                           |
| Constitution Check           | `^## Constitution Check.*$`                                                | `## Constitution Check *(mandatory)*`                                                                    |
| Engaged Principles           | `^\*\*Engaged Principles\*\*: (.+)$`                                       | `**Engaged Principles**: VII (Canonical Representation)...`                                              |
| Compliance Notes             | `^\*\*Compliance Notes\*\*:?`                                              | `**Compliance Notes**:`                                                                                  |
| Requirements header          | `^## Requirements.*$`                                                      | `## Requirements *(mandatory)*`                                                                          |
| FR requirement               | `^-\s+\*\*FR-(\d{3})\*\*: (.+)$`                                           | `- **FR-001**: The CFM Builder MUST accept an EvidenceGraph...`                                          |
| Key Entities header          | `^### Key Entities.*$`                                                     | `### Key Entities *(include if feature involves data)*`                                                  |
| Entity definition            | `^-\s+\*\*(.+)\*\*: (.+)$`                                                 | `- **CanonicalFunctionalModel**: The top-level container...`                                             |
| Success Criteria header      | `^## Success Criteria.*$`                                                  | `## Success Criteria *(mandatory)*`                                                                      |
| SC item                      | `^-\s+\*\*SC-(\d{3})\*\*: (.+)$`                                           | `- **SC-001**: An evidence graph containing 500 elements...`                                             |
| Assumptions header           | `^## Assumptions$`                                                         | `## Assumptions`                                                                                         |
| Assumption item              | `^-\s+(.+)$` (under Assumptions section)                                   | `- The EvidenceGraph from F05 provides sufficient semantic type information...`                          |
| Future Work header           | `^## Future Work$`                                                         | `## Future Work`                                                                                         |
| Future Work item             | `^-\s+\*\*(.+)\*\*: (.+)$`                                                 | `- **Glossary linking**: Automatically linking glossary terms...`                                        |

**Specific content patterns discovered:**

User Story priority patterns from real files:

```
P1 — Core functionality (MVP)
P2 — Important but not blocking
P3 — Nice to have
```

Evidence reference pattern found across specs:

```
**Evidence**: {document_id}::{section_id} — {text_fragment}
```

Cross-reference patterns:

```
F<NN>   — Feature/Spec reference (e.g., F27, F03, F05-F11)
FR-NNN  — Functional Requirement reference
SC-NNN  — Success Criterion reference
```

#### 2. `plan.md` — Implementation Plan (present in 027 of 29 features)

| Section             | Regex Pattern                                                                          | Example                                                                  |
| ------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ | --------------------------------------------------------- |
| Plan title          | `^# Implementation Plan: (.+)$`                                                        | `# Implementation Plan: Canonical Functional Model Builder`              |
| Branch + Date       | `^\*\*Branch\*\*: \`(\d{3}-[a-z0-9-]+)\`\s*\|\s*\*\*Date\*\*: (\d{4}-\d{2}-\d{2}).\*$` | `**Branch**: \`007-canonical-functional-model\` \| **Date**: 2026-07-16` |
| Summary             | `^## Summary$`                                                                         | `## Summary`                                                             |
| Tech Context        | `^## Technical Context$`                                                               | `## Technical Context`                                                   |
| Language            | `^\*\*Language/Version\*\*: (.+)$`                                                     | `**Language/Version**: Python 3.13`                                      |
| Dependencies        | `^\*\*Primary Dependencies\*\*: (.+)$`                                                 | `**Primary Dependencies**: networkx, pydantic`                           |
| Testing             | `^\*\*Testing\*\*: (.+)$`                                                              | `**Testing**: pytest, ruff`                                              |
| Platform            | `^\*\*Target Platform\*\*: (.+)$`                                                      | `**Target Platform**: Linux, macOS, Windows`                             |
| Performance         | `^\*\*Performance Goals\*\*: (.+)$`                                                    | `**Performance Goals**: 500 elements in < 3s`                            |
| Constraints         | `^\*\*Constraints\*\*: (.+)$`                                                          | `**Constraints**: Must not introduce new dependencies`                   |
| Constitution Check  | `^## Constitution Check$`                                                              | `## Constitution Check`                                                  |
| Gate marker         | `^\*GATE: (.+)\*$`                                                                     | `*GATE: Review engaged principles before planning*`                      |
| Compliance list     | `^\*\*Compliance Verifications\*\*:`                                                   | `**Compliance Verifications**:`                                          |
| Compliance checkbox | `^- \[([ x])\] (.+)$`                                                                  | `- [x] VII (Canonical Representation) ...`                               |
| Gate result         | `^\*\*Gate result\*\*: (PASS                                                           | FAIL) — (.+)$`                                                           | `**Gate result**: PASS — All engaged principles verified` |
| Project Structure   | `^## Project Structure$`                                                               | `## Project Structure`                                                   |
| Complexity          | `^## Complexity Tracking$`                                                             | `## Complexity Tracking`                                                 |

#### 3. `tasks.md` — Implementation Tasks (present in 027 of 29 features)

| Section          | Regex Pattern                                                           | Example                                                                  |
| ---------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------ | ---------------------------- |
| YAML frontmatter | `^---$` (delimiter)                                                     | `---\ndescription: "Task list for ..."\n---`                             |
| Tasks title      | `^# Tasks: (.+)$`                                                       | `# Tasks: Measurement Engine Plugin — Business Complexity Points (BCP)`  |
| Input reference  | `^\*\*Input\*\*: (.+)$`                                                 | `**Input**: Design documents from \`specs/026-...\``                     |
| Prerequisites    | `^\*\*Prerequisites\*\*: (.+)$`                                         | `**Prerequisites**: plan.md (required), spec.md (required)`              |
| Organization     | `^\*\*Organization\*\*: (.+)$`                                          | `**Organization**: Tasks are grouped by user story...`                   |
| Format spec      | `^## Format: .+$`                                                       | `## Format: \`[ID] [P?] [Story] Description\``                           |
| Task line        | `^-\s+\[([ xX])\]\s+(T\d{3})(?:\s+\[P\])?\s*(?:\[(US[1-4])\])?\s*(.+)$` | `- [x] T004 [P] [US1] Create story generator in ...`                     |
| Phase header     | `^## Phase (\d+): (.+)$`                                                | `## Phase 2: Foundational (Blocking Prerequisites)`                      |
| Phase purpose    | `^\*\*Purpose\*\*: (.+)$`                                               | `**Purpose**: Core models, story generator, SDK adapter`                 |
| Phase checkpoint | `^\*\*Checkpoint\*\*: (.+)$`                                            | `**Checkpoint**: Foundation ready — all models exist`                    |
| Critical marker  | `^⚠️ CRITICAL: (.+)$`                                                   | `⚠️ CRITICAL: No user story work can begin until...`                     |
| MVP marker       | `^🎯 MVP$`                                                              | `🎯 MVP`                                                                 |
| Story section    | `^### (Tests                                                            | Implementation) for User Story (\d+)$`                                   | `### Tests for User Story 1` |
| Story goal       | `^\*\*Goal\*\*: (.+)$`                                                  | `**Goal**: Software estimator runs \`specmetrics measure --method bcp\`` |
| Story test ref   | `^\*\*Independent Test\*\*: (.+)$`                                      | `**Independent Test**: \`pytest tests/unit/...\``                        |
| Parallel marker  | `\[P\]` inside task line                                                | `[P]`                                                                    |
| User Story ref   | `\[US[1-4]\]` inside task line                                          | `[US1]`                                                                  |

#### 4. `data-model.md` — Data Model (present in 027 of 29 features)

| Pattern                         | Description                     | Example                                              |
| ------------------------------- | ------------------------------- | ---------------------------------------------------- |
| `^# Data Model: (.+)$`          | Data model title                | `# Data Model: Canonical Functional Model Builder`   |
| `^## (.+)$`                     | Entity/section header           | `## CanonicalFunctionalModel`                        |
| `^\| (\w+) \| (.+) \| (.+) \|$` | Table: Field, Type, Description | `\| run_id \| str \| Unique execution identifier \|` |
| `^\| --- \| --- \| --- \|$`     | Table separator                 | `\| --- \| --- \| --- \|`                            |
| `^### (.+)`                     | Sub-section                     | `### Validation Rules`                               |

#### 5. `research.md` — Research (present in 027 of 29 features)

| Pattern                             | Description         | Example                                         |
| ----------------------------------- | ------------------- | ----------------------------------------------- |
| `^# Research: (.+)$`                | Research title      | `# Research: Deterministic Semantic Engine`     |
| `^\*\*Decision\*\*: (.+)$`          | Decision made       | `**Decision**: Use content-hash IDs`            |
| `^\*\*Rationale\*\*: (.+)$`         | Rationale           | `**Rationale**: Ensures deterministic identity` |
| `^\*\*Alternatives considered\*\*:` | Alternatives header | `**Alternatives considered**:`                  |

#### 6. `quickstart.md` — Quickstart/Validation (present in 027 of 29 features)

| Pattern                            | Description        | Example                                                        |
| ---------------------------------- | ------------------ | -------------------------------------------------------------- |
| `^# Quickstart: (.+)$`             | Quickstart title   | `# Quickstart: Semantic Extraction Engine`                     |
| `^## Validation Scenarios$`        | Validation section | `## Validation Scenarios`                                      |
| `^### Scenario (\d+): (.+)$`       | Scenario header    | `### Scenario 1: Pipeline completes with deterministic engine` |
| `^\*\*Expected outcome\*\*: (.+)$` | Expected outcome   | `**Expected outcome**: The pipeline completes successfully`    |

#### 7. `checklists/requirements.md` — Quality Checklist (features 001–009)

| Pattern                                     | Description     | Example                                                  |
| ------------------------------------------- | --------------- | -------------------------------------------------------- |
| `^# Specification Quality Checklist: (.+)$` | Checklist title | `# Specification Quality Checklist: MVP Release Outline` |
| `^\*\*Purpose\*\*: (.+)$`                   | Purpose         | `**Purpose**: Validate specification completeness`       |
| `^## (.+)$`                                 | Section header  | `## Content Quality`, `## Requirement Completeness`      |
| `^- \[([ x])\] (.+)$`                       | Checklist item  | `- [ ] No implementation details`                        |

#### 8. `contracts/*.md` — Interface Contracts (features 002–028)

| Pattern                   | Description       | Example                                 |
| ------------------------- | ----------------- | --------------------------------------- |
| `^# (.+) Contract$`       | Contract title    | `# Canonical Functional Model Contract` |
| `^## Interface$`          | Interface section | `## Interface`                          |
| `^class \w+\(Protocol\):` | Protocol class    | `class CFMConsumer(Protocol):`          |
| `^## Contract Rules$`     | Rules section     | `## Contract Rules`                     |
| `^\d+\. (.+)$`            | Numbered rule     | `1. Input: An EvidenceGraph instance`   |

### Specific Cross-File Reference Patterns Discovered

**FR/SC cross-references (across all spec files):**

```
\bFR-\d{3}\b     — Functional Requirement (e.g., FR-001)
\bSC-\d{3}\b     — Success Criterion (e.g., SC-006)
\bT\d{3}\b       — Task ID (e.g., T004)
\bF\d{2}\b       — Feature/Spec cross-reference (e.g., F27, F03, F05-F11)
\bUS[1-4]\b      — User Story reference (e.g., US1)
\[P[1-3]\]        — Priority marker
\[P\]             — Parallel task marker
```

**Task checkbox patterns (from real tasks.md files):**

```
- [ ] T001 Create ...     → pending task
- [x] T001 Create ...     → completed task
- [X] T001 Create ...     → completed task (alternative)
- [x] T004 [P] [US1] ...  → completed parallel task for US1
```

**Section separator pattern:**

```
^---$ (3 or more dashes on a line by themselves)
```

**Metadata/reference patterns:**

```
Input: spec.md (required), plan.md (required), research.md, data-model.md, contracts/
Prerequisites: plan.md (required), spec.md (required for user stories)
```

### Summary Statistics (from actual file analysis)

| File Type                    | Count              | Present In             |
| ---------------------------- | ------------------ | ---------------------- |
| `spec.md`                    | 29                 | All features (001–029) |
| `plan.md`                    | 27                 | 002–028                |
| `tasks.md`                   | 27                 | 002–028                |
| `data-model.md`              | 27                 | 002–028                |
| `research.md`                | 27                 | 002–028                |
| `quickstart.md`              | 27                 | 002–028                |
| `contracts/`                 | 27 dirs (37 files) | 002–028                |
| `checklists/requirements.md` | 9                  | 001–009 only           |

## OpenSpec Format Analysis _(discovered from FlowSource analysis; examples in tests/openspec/)_

A real OpenSpec repository (FlowSource) was analyzed for pattern discovery. Its documents — 29 domain capabilities, 3 active changes, 28 archived changes, ~2760 lines of specification content — are included as examples in `tests/openspec/` for end-to-end test scenarios of specmetrics.

### Directory Structure

```
openspec/
├── specs/                                  # Master specifications
│   ├── flow-indicators/spec.md             # One directory per domain/capability
│   ├── dominance-classifiers/spec.md
│   ├── gui-interface/spec.md
│   └── ... (29 domains total)
└── changes/
    ├── diagnosis-panel/                    # Active change
    │   ├── .openspec.yaml                  # Metadata: schema, created date
    │   ├── proposal.md                     # Why, What Changes, Capabilities, Impact
    │   ├── design.md                       # Context, Goals, Decisions, Risks
    │   ├── tasks.md                        # Implementation checklist
    │   └── specs/                          # Delta specifications
    │       ├── diagnosis-panel/spec.md     # ADDED Requirements
    │       ├── liquidity-classifier/spec.md
    │       ├── institutional-classifier/spec.md
    │       └── dominance-classifiers/spec.md
    ├── archive/                            # Completed/archived changes
    │   └── YYYY-MM-DD-<name>/
    │       ├── .openspec.yaml
    │       ├── proposal.md
    │       ├── design.md
    │       ├── tasks.md
    │       └── specs/                      # Delta specs (subdir or .spec.delta.md)
    ├── eficiencia-do-movimento/            # Active change
    │   └── ... (same structure as above)
    └── participation-negociacoes/          # Active change
        └── ... (same structure as above)
```

Total: 29 domain specs, 3 active changes, 38 archived changes.

### Document Types and Their Sections

| Artifact          | Path Pattern                                  | Sections Discovered                                                                                                    |
| ----------------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Master spec       | `specs/<domain>/spec.md`                      | `## Purpose`, `## Requirements`, `### Requirement: <Title> (<ID>)`, `#### Scenario: <name>`, GIVEN/WHEN/THEN/AND lists |
| Delta spec (dir)  | `changes/<name>/specs/<domain>/spec.md`       | `## ADDED Requirements`, `## MODIFIED Requirements`, `### Requirement: ...`                                            |
| Delta spec (flat) | `changes/<name>/specs/<domain>.spec.delta.md` | `## Purpose`, `## Modified Requirements`, `### Requirement: <Title> (<substitui note>)`                                |
| No-change spec    | `changes/<name>/specs/spec.md`                | Literal "No specification changes required for this change."                                                           |
| No-change index   | `changes/<name>/specs/_index.md`              | `# Specs — <name>`, Portuguese justification paragraph                                                                 |
| No-change README  | `changes/<name>/specs/README.md`              | `# Specs — <name>`, `## Justificativa` justification                                                                   |
| Proposal          | `changes/<name>/proposal.md`                  | `## Why`, `## What Changes`, `## Capabilities` → `### New Capabilities`, `### Modified Capabilities`, `## Impact`      |
| Design            | `changes/<name>/design.md`                    | `## Context`, `## Goals / Non-Goals`, `## Decisions` → `### <N>. <Title>`, `## Risks / Trade-offs`                     |
| Tasks             | `changes/<name>/tasks.md`                     | `## <N>. <Category>`, `- [ ] <N.N> <description>`, `- [x] <N.N> <description>`                                         |
| Metadata          | `.openspec.yaml`                              | `schema: spec-driven\`, `created: YYYY-MM-DD`                                                                          |

### Discovered Section Heading Patterns (regex-ready)

```
## Purpose                          — Domain purpose/overview
## Requirements                     — All requirements block
## ADDED Requirements               — Delta: new requirements added
## MODIFIED Requirements            — Delta: existing requirements changed
### Requirement: <Title> (<ID>)     — Single requirement (ID optional: FS201, DC301, etc.)
### Requirement: <Title> (<replace note>)  — Delta: "substitui <old requirement>"
#### Scenario: <description>       — Test scenario with GIVEN/WHEN/THEN
- **GIVEN** <precondition>         — Given/And context
- **WHEN** <action>                — When trigger
- **THEN** <expected>              — Then expected behavior
- **AND** <additional>             — Additional clause
## Why                             — Change rationale (proposal.md)
## What Changes                    — Change description (proposal.md)
## Capabilities                    — Capability list (proposal.md)
### New Capabilities               — New capabilities sub-section
### Modified Capabilities          — Modified capabilities sub-section
## Impact                          — Impact analysis (proposal.md)
## Context                         — Design context (design.md)
## Goals / Non-Goals               — Scope definition (design.md)
## Decisions                       — Decision records (design.md)
### Decision <N>: <Title>          — Individual decision (colon separator)
### <N>. <Title>                   — Individual decision (dot separator variant)
## Risks / Trade-offs              — Risk assessment (design.md)
## <N>. <Category>                 — Task category heading (tasks.md)
# Specs — <name>                  — No-change wrapper heading (_index.md, README.md)
## Justificativa                   — No-change justification (README.md)
```

### Discovered Content Patterns (regex-ready)

**Requirement statements (Portuguese):**

```
O sistema DEVE <action>
O sistema NÃO DEVE <action>
<subject> DEVE <action>
<subject> DEVEM <action>
<subject> NÃO DEVE <action>
DEVE ser <expected>
DEVE retornar <value>
DEVE exibir <message>
DEVE baixar <resource>
DEVE manter <state>
DEVE usar <mechanism>
```

**Requirement statements (English):**

```
The system SHALL <action>
The system SHALL NOT <action>
<component> SHALL <action>
SHOULD <action>
MAY <action>
```

**Capability ID prefixes (extracted from real files):**

```
FS###  — Flow/Feature Spec (FS201, FS202, ..., FS401-FS403, FS601-FS607, FS101, FS301)
DC###  — Dominance Classifier (DC301-DC304)
DR###  — Dominance Ranking (DR101-DR106)
DT###  — Dominance Timeline (DT201-DT209)
DP###  — Diagnosis Panel (DP101-DP107)
IC###  — Institutional Classifier (IC101-IC103)
LC###  — Liquidity Classifier (LC101-LC103)
REQ-   — Engineering standard requirements
```

**Decision record patterns (design.md):**

```
### Decision <N>: <Title>              — English format (colon)
### <N>. <Title>                       — Portuguese format (dot)
<description paragraph(s)>
**Rationale**: <reasoning>             — English rationale
**Alternative considered**: <other>    — English alternative
**Alternativa considerada:** <other>   — Portuguese alternative
```

**Risk/Trade-off patterns (design.md):**

```
- [Risk] <description> → Mitigation: <action>
- [Trade-off] <description> → Acceptable because <reason>
- **<risk-title>**: <desc> **Mitigação:** <action>    — Portuguese inline format
```

**Task checklist patterns (tasks.md) — bilingual:**

```
## 1. Category (Portuguese)
- [x] 1.1 <task>           — completed
- [ ] 1.2 <task>           — pending

## 2. Category (English)
- [ ] 2.1 <task>           — pending
- [x] 2.2 <task>           — completed
```

**Proposal capability description patterns:**

```
### New Capabilities
- `<capability-id>`: <description>     — kebab-case ID + colon description

### Modified Capabilities
- `<domain>`: <change description>     — domain name + colon + specifics
- *(nenhuma — capability nova)*        — negative indicator (parenthesized asterisk)
```

**Impact section patterns (proposal.md):**

```
- **<file path>** — <description>      — file impact list items
- **Target**: Release X.Y.Z             — version targeting
- **Novo arquivo**: <path> (~N linhas)  — new file with line estimate
- **Modificado**: <path> — <desc>       — modified file
- **Nenhuma mudança em** <area>         — negative scope declaration
```

**Inline code and example patterns:**

````
(ex: `["VALE3", "PETR4", "ITUB4", ...]`)   — inline examples
```python [...]```                           — language-annotated code blocks
`_method_name_`                              — italicized code references (method calls)
`<capability-id>`                            — kebab-case identifiers in backticks
````

**HTML comment patterns (non-rendered metadata):**

```
<!-- HTML comment with explanatory text -->  — non-rendered notes in proposals
```

**Scenario patterns (extracted from real files):**

```
- **WHEN** CLV entre −1.00 e −0.70           (range conditions)
- **WHEN** MaxPric = 80, MinPric = 70         (variable assignments)
- **WHEN** o usuário clica no botão "IBOV"    (user actions with quotes)
- **THEN** a classificação DEVE ser "Venda Muito Forte" com score numérico −3
- **THEN** CLV DEVE ser ((75 − 70) − (80 − 75)) / (80 − 70) = 0
- **THEN** o sistema DEVE exibir "Sem dados" centralizado
- **WHEN** a API B3 retorna erro para uma data solicitada
- **WHEN** a lista de tickers está vazia
```

### Bilingual Pattern Analysis

The OpenSpec repository is bilingual (Portuguese primary, English mixed). Key patterns:

| Pattern          | Portuguese                                 | English                       | Frequency        |
| ---------------- | ------------------------------------------ | ----------------------------- | ---------------- |
| Requirement verb | `DEVE` / `NÃO DEVE`                        | `SHALL` / `SHALL NOT`         | PT: 90%, EN: 10% |
| Scenario keyword | `GIVEN` / `WHEN` / `THEN` / `AND`          | Same (English)                | 100% English     |
| Decision title   | `### <N>. <Title>`                         | `### Decision <N>: <Title>`   | PT: 40%, EN: 60% |
| Rationale label  | `**Alternativa considerada:**`             | `**Alternative considered:**` | PT: 30%, EN: 70% |
| Task language    | Mixed (PT headers, EN tasks or vice versa) | —                             | Mixed            |
| Proposal why     | Portuguese                                 | English (rare)                | PT: 95%          |
| Design context   | Portuguese                                 | English (rare)                | PT: 90%          |

### Delta Spec Variants

**Variant 1 — Subdirectory format** (active changes, e.g., `diagnosis-panel/specs/dominance-classifiers/spec.md`):

```
## ADDED Requirements
### Requirement: <Title> (<ID>)
<requirement body>
#### Scenario: <title>
- **WHEN** ...
- **THEN** ...

## MODIFIED Requirements
### Requirement: <Title> (<ID>) — <change description>
<requirement body>
```

**Variant 2 — Flat `.spec.delta.md` format** (archived changes, e.g., `index-portfolio-buttons/specs/data-ingestion.spec.delta.md`):

```
## Purpose
<single paragraph describing the delta>

## Modified Requirements
### Requirement: <Title> (substitui "<old requirement>")
<requirement body>
#### Scenario: <title>
- **WHEN** ...
- **THEN** ...
```

**Variant 3 — No-change declaration** (when a change does not alter specs):

```
# Specs — <name>
<paragraph: "No specification changes required for this change.">
```

or:

```
# Specs — <name>
## Justificativa
<justification paragraph>
```

**Key delta pattern to detect** — `(substitui "...")` in delta requirement headings indicates a MODIFIED (not ADDED) requirement.

### Domain Entities Discovered examples (for Data Group extraction)

From 29 domain specs + change artifacts of the example repository (flowscope), these domain entities emerge as extractable CFM data groups:

```
TradeDay, AggregatedMetrics, DominanceClassification, ConvictionClassification,
MoneyFlowClassification, InstitutionalClassification, LiquidityClassification,
DirectionDiagnosis, MoneyFlowDiagnosis, ConvictionDiagnosis, InstitutionalDiagnosis,
LiquidityDiagnosis, Diagnosis, TickerList, OrientationPanel, PriceRangePanel,
FinancialFlowPanel, DominanceTimelineChart, DiagnosisPanel, ClassificationBar,
CLVGauge, BuySellBar, PriceRangeDiagram, B3Client, B3DataRepository, CacheManager,
IndicatorEngine, AnalyzeTickersUseCase, FlowScopeGUI, EfficiencyClassification,
EfficiencyPanel, ParticipationPanel, IndexCache, ChartEmptyState
```

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Speckit specialist fallback extracts full semantic model from feature specs (Priority: P1)

An end-to-end test runs `specmetrics measure` on a SpecKit repository. The deterministic fallback specialist for speckit scans all feature workspace artifacts (`spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `checklists/`) and applies regex extraction rules tailored to the Speckit format. Every structural element required by CFM (actors, functional processes, business rules, data groups, operations, relationships) and CSM (decisions, assumptions, constraints, risks, open questions, acceptance criteria, glossary terms) is populated from the raw Markdown content — no LLM required. The pipeline completes all stages end-to-end and produces valid measurements.

**Why this priority**: The primary goal is to use the deterministic fallback as the main e2e testing mechanism. Without speckit specialist rules, SpecKit repositories can only be partially extracted by the generic heading-based rules.

**Independent Test**: Can be tested by running `specmetrics measure` on a SpecKit repository containing multiple feature workspaces with known content, and verifying that CFM has non-empty actors, functional_processes, business_rules, data_groups, and CSM has non-empty decisions, assumptions, constraints, acceptance_criteria.

**Acceptance Scenarios**:

1. **Given** a SpecKit repository with 5+ feature workspaces each containing `spec.md`, `plan.md`, `tasks.md`, **When** the pipeline runs with deterministic engine, **Then** CFM contains at least 3 actors, 3 functional processes, 3 business rules, 3 data groups identified from the specs.
2. **Given** feature specs with explicit "Actors", "User Stories", "Requirements", "Success Criteria" and "Assumptions" sections, **When** the speckit specialist processes them, **Then** CSM contains at least 2 assumptions, 2 decisions, 2 acceptance criteria, 2 constraints.
3. **Given** a SpecKit repository, **When** the pipeline completes the measure command, **Then** all measurement plugins (FPA, SFP, SNAP, Token Points, Cognitive Points, Story Points, T-Shirt, BCP) produce non-zero outputs.

---

### User Story 2 - OpenSpec specialist extracts CFM/CSM from OpenSpec master specs, change proposals, designs, and delta specs (Priority: P1)

An end-to-end test runs `specmetrics measure` on the OpenSpec examples in `tests/openspec/` (29 domain capabilities, 3 active changes, 38 archived changes). The OpenSpec specialist processes each document type with dedicated regex patterns:

- **Master specs** (`specs/<domain>/spec.md`): Extract `## Purpose` sections as functional process descriptions; `### Requirement: <Title>` blocks as business rules with `O sistema DEVE` / `The system SHALL` statements; `#### Scenario:` blocks with GIVEN/WHEN/THEN/AND as operations with pre/postconditions; capability IDs (FS###, DC###, DR###, etc.) as data group references.
- **Delta specs (dir format)** (`changes/<name>/specs/<domain>/spec.md`): Distinguish `## ADDED Requirements` from `## MODIFIED Requirements` — added requirements produce CFM elements; modified requirements produce CSM decision elements with change provenance.
- **Delta specs (flat format)** (`changes/<name>/specs/<domain>.spec.delta.md`): Extract `## Purpose` as change summary, `## Modified Requirements` with `(substitui "...")` markers as CSM change provenance.
- **No-change variants** (`specs/spec.md`, `_index.md`, `README.md`): Detect and skip — produce no extraction elements, avoiding false positives.
- **Proposals** (`proposal.md`): Extract `## Why` as CFM rationale/process; `## What Changes` list items as operations; `## Capabilities` as functional process definitions distinguishing New vs Modified (via `### New Capabilities` and `### Modified Capabilities` subheadings); `## Impact` file list as CSM constraints with `**Target**: Release` version metadata.
- **Designs** (`design.md`): Extract `### Decision <N>: <Title>` (colon separator) and `### <N>. <Title>` (dot separator, Portuguese) blocks as CSM Decision elements with rationale and alternatives (both `**Alternative considered:**` English and `**Alternativa considerada:**` Portuguese); `## Risks / Trade-offs` as CSM Risk elements with mitigation; `## Goals / Non-Goals` as CSM assumptions/constraints.
- **Tasks** (`tasks.md`): Extract numbered checklist sections as CSM specification activities with `- [ ]`/`- [x]` markers indicating completion status. Bilingual support for both Portuguese and English task descriptions.

CFM actors are extracted from inline entity references (Usuário, Sistema, Cliente, Analista, B3Client, IndicatorEngine, etc.). Business rules from `DEVE`/`SHALL` statements. Data groups from domain entity names (TradeDay, Diagnosis, DominanceClassification, ParticipationPanel, etc.). Operations from `#### Scenario:` blocks and `- **WHEN** <action>` lines. Decision records from `### Decision <N>:` and `### <N>.` headings with `**Rationale:**`, `**Alternative considered:**`, `**Alternativa considerada:**` field labels.

**Why this priority**: OpenSpec is the second supported framework. The `tests/openspec/` examples with 29 domains and 38 changes provide a rich, real-world validation corpus for e2e deterministic testing.

**Independent Test**: Can be tested by running `specmetrics measure --repo tests/openspec/ --engine deterministic --stage extract` and verifying that extraction produces at least 40 elements from master specs, 15 from proposals, 10 from designs, 20 from delta specs — all without any LLM.

**Acceptance Scenarios**:

1. **Given** the OpenSpec examples in `tests/openspec/` with 29 domain specs, **When** the pipeline runs deterministic extraction, **Then** CFM contains at least 5 actors (Usuário, Sistema, B3Client, IndicatorEngine, AnalyzeTickersUseCase), at least 10 business rules from `DEVE`/`SHALL` statements, and at least 5 data groups (TradeDay, DominanceClassification, Diagnosis, TickerList, OrientationPanel).
2. **Given** change artifacts including `proposal.md`, `design.md`, and `tasks.md`, **When** the openspec specialist processes them, **Then** CSM contains at least 2 decisions from `### Decision <N>:` and `### <N>. <Title>` blocks, at least 2 risks from `## Risks / Trade-offs` sections or `- [Risk]` list items, and at least 2 specification activities from tasks sections.
3. **Given** delta specs with `## ADDED Requirements` and `## MODIFIED Requirements` markers, **When** processed, **Then** ADDED requirements produce CFM business rule elements and MODIFIED requirements produce CSM decision elements. The `(substitui "...")` parenthetical in flat `.spec.delta.md` requirement titles is detected as change provenance.
4. **Given** `#### Scenario:` blocks with GIVEN/WHEN/THEN/AND lists, **When** processed, **Then** each WHEN clause produces a CFM operation element and each THEN clause produces a CFM business rule element.
5. **Given** `design.md` files with decisions in both `### Decision <N>: <Title>` (English) and `### <N>. <Title>` (Portuguese) formats, **When** processed, **Then** both formats are recognized and produce CSM Decision elements. Portuguese `**Alternativa considerada:**` labels are parsed as alternative fields with the same semantics as English `**Alternative considered:**`.

---

### User Story 3 - Regex-based extraction rules cover all CFM and CSM entity types (Priority: P1)

A developer inspects the extraction output from the deterministic fallback. Every entity type required by the Canonical Functional Model (actors, functional processes, business rules, data groups, operations, relationships) and the Canonical Specification Model (decisions, assumptions, constraints, risks, open questions, acceptance criteria, glossary terms) is represented. No entity category is empty unless the source spec genuinely lacks that content.

**Why this priority**: The fallback must feed everything that "specmetrics measure" needs. Empty entity categories cause measurement plugins to produce zero or incomplete results.

**Independent Test**: Can be tested by running the deterministic pipeline on a spec that explicitly contains content for all categories and verifying every CFM and CSM category has at least one element.

**Acceptance Scenarios**:

1. **Given** a spec document that explicitly defines actors, business rules, data, processes, decisions, assumptions, constraints, risks, questions, acceptance criteria, and glossary terms, **When** the deterministic specialist processes it, **Then** all 14 entity categories across CFM and CSM contain at least one element.
2. **Given** a minimal spec with only a title and description, **When** processed, **Then** the CFM and CSM outputs have empty collections for most entity types but the pipeline does not fail.

---

### User Story 4 - Framework-specific rule packs replace current minimal versions (Priority: P2)

The current framework rule packs (`openspec_rules.yaml`, `speckit_rules.yaml`) contain only heading-based rules (Feature, Scenario, Background for speckit; Use Case, Actor, Requirement, Precondition for openspec). The new specialist rule packs extend these with rich regex patterns that extract semantic elements from the full content of Markdown sections — list items, table rows, keyword patterns, GWT scenarios, requirement statements, and glossary definitions.

**Why this priority**: The current rules are too minimal to populate CFM and CSM for any meaningful e2e test. Richer rules are the key enabler for the primary goal.

**Independent Test**: Can be tested by comparing the element count and type diversity between the old and new rule packs on the same document set — the new pack produces more elements and more varied types.

**Acceptance Scenarios**:

1. **Given** a SpecKit spec with User Stories, Given/When/Then scenarios, and requirement tables, **When** processed with the new speckit specialist rules, **Then** the output contains at least 10 extracted elements, compared to at most 3 with the old rules.
2. **Given** an OpenSpec spec with Use Case descriptions, Actor definitions, and Precondition lists, **When** processed with the new openspec specialist rules, **Then** the output contains at least 8 extracted elements, compared to at most 4 with the old rules.

---

### Edge Cases

- What happens if a repository uses both Speckit and OpenSpec conventions? The deterministic engine auto-detects the framework from document metadata and loads the corresponding specialist rule pack. Framework detection already exists in `_load_framework_packs()`.
- How are conflicts between specialist rules and generic rules resolved? Priority-based conflict resolution (numeric priority 1–100), already implemented in `DeterministicSemanticEngine._load_rules()`.
- What happens when a regex rule matches content that is not semantically meaningful? The rule confidence scores filter low-quality matches. Rules with confidence below 0.70 are deprioritized; the CFM classifier already handles noise through the `unclassified` category.
- How does the system handle documents that don't follow the expected regex patterns? Generic rules from `default_rule_pack.yaml` still apply as a baseline. Specialist rules are additive — they never override the structural baseline.
- How are extraction rule match/miss results surfaced for debugging? The deterministic engine emits structured debug output containing: per-rule match trace (document ID, section, matched text, confidence), unmatched pattern statistics grouped by pattern ID and document type, and a coverage summary (patterns attempted vs. patterns matched per document). This output is produced alongside the canonical CFM/CSM elements, not as a replacement — it feeds the e2e testing pipeline's validation stage.

## Constitution Check _(mandatory)_

**Engaged Principles**: I (Specification First), III (Semantic Before Structural), IV (LLM-Assisted, Deterministic Results), V (Evidence First), VII (Canonical Representation), IX (Rule Externalization), XIV (Layer Independence)

**Compliance Notes**:

- Specification First (I): Specialist fallbacks consume normalized Document objects from the Specification Adapter layer — they operate on specifications as the primary source.
- Semantic Before Structural (III): Regex rules extract semantic meaning (actors, business rules, decisions, etc.) from Markdown structure, transforming document format into functional knowledge.
- LLM-Assisted, Deterministic Results (IV): The specialist fallbacks are purely deterministic — no LLM involvement. All extraction is rule-based, producing repeatable, auditable results.
- Evidence First (V): Every extracted element preserves its source evidence — document ID, section reference, and text fragment — via the existing EvidenceReference model.
- Canonical Representation (VII): Specialist fallbacks produce ExtractedElement objects in the canonical model. Downstream CFM/CSM builders consume these without knowing whether extraction was deterministic or LLM-assisted.
- Rule Externalization (IX): Specialist rules are organized as external rule pack YAML files. Organizations can customize or extend them without modifying engine code.
- Layer Independence (XIV): Specialist fallbacks implement the `SemanticExtractionEngine` interface. The pipeline invokes only this interface. No layer knows whether extraction used generic rules or specialist rules.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The Speckit specialist rule pack MUST extract Actors from `^-\s+\*\*(.+)\*\*: (.+)$` entity definition patterns under a `### Key Entities` section when the term starts with an uppercase role-like word (User, Actor, Developer, Analyst, Consumer, Plugin, System) — using `semantic_type: entity` with confidence 0.85. The entity name becomes the Actor name for CFM.
- **FR-002**: The Speckit specialist rule pack MUST extract User Stories from `^### User Story (\d+) [—–-] (.+) \(Priority: (P[1-3])\)` headings — the story title and number produce a CFM functional process with `semantic_type: entity` and confidence 0.95. The priority label `(P1)`/`(P2)`/`(P3)` is stored as metadata.
- **FR-003**: The Speckit specialist rule pack MUST extract `^\*\*Why this priority\*\*: (.+)$` text following each User Story as a business rule justification with `semantic_type: fact` and confidence 0.80.
- **FR-004**: The Speckit specialist rule pack MUST extract acceptance scenarios from numbered GIVEN/WHEN/THEN patterns: `^(\d+)\. \*\*Given\*\* (.+), \*\*When\*\* (.+), \*\*Then\*\* (.+)$` — the Given text becomes a precondition fact, the When text becomes an operation trigger, and the Then text becomes an assertion fact. Each clause gets `semantic_type: fact` with confidence 0.90.
- **FR-005**: The Speckit specialist rule pack MUST extract multi-line GIVEN/WHEN/THEN patterns: `^-\s+\*\*Given\*\* (.+)$` / `^-\s+\*\*When\*\* (.+)$` / `^-\s+\*\*Then\*\* (.+)$` as individual elements with `semantic_type: fact` and confidence 0.90. `^-\s+\*\*And\*\* (.+)$` following a THEN is merged into the same assertion.
- **FR-006**: The Speckit specialist rule pack MUST extract requirements from `^-\s+\*\*FR-(\d{3})\*\*: (.+)$` — the FR number becomes an ID reference (data group), the description text becomes a business rule with `semantic_type: fact` and confidence 0.95. The full requirement text including system capability verbs (MUST, SHOULD, MAY) is preserved.
- **FR-007**: The Speckit specialist rule pack MUST extract success criteria from `^-\s+\*\*SC-(\d{3})\*\*: (.+)$` — the SC number becomes an ID reference, the description becomes an acceptance criterion element with `semantic_type: fact` and confidence 0.95. Content is also matched against CSM acceptance_criterion patterns.
- **FR-008**: The Speckit specialist rule pack MUST extract Key Entities from `^-\s+\*\*(.+)\*\*: (.+)$` lines under a `### Key Entities` section — the bold term becomes an entity/actor/data group name with `semantic_type: entity` and confidence 0.90. Classification follows CFM classifier heuristics (TitleCase → data_group, role suffix → actor).
- **FR-009**: The Speckit specialist rule pack MUST extract Assumptions from `^-\s+(.+)$` lines under the `## Assumptions` section — each line becomes an assumption element matching CSM assumption patterns with confidence 0.90.
- **FR-010**: The Speckit specialist rule pack MUST extract Constitution Check engaged principles from `^\*\*Engaged Principles\*\*: (.+)$` — each Roman numeral principle reference (VII, XIV, V, etc.) becomes a CSM constraint element with confidence 0.95.
- **FR-011**: The Speckit specialist rule pack MUST extract Edge Cases from `^-\s+What happens (.+)\? (.+)$` under the `### Edge Cases` section — the question becomes an open question element matching CSM open_question patterns with confidence 0.85. The answer (after the `?`) becomes the context.
- **FR-012**: The Speckit specialist rule pack MUST extract `^-\s+\*\*IMP-\d+\*\*: (.+)$` clarification implementation note lines as CSM decision elements with `activity_type: refinement` and confidence 0.90 — each IMP entry documents an implementation decision made during specification.
- **FR-013**: The Speckit specialist rule pack MUST extract task lines from `tasks.md` files matching `^-\s+\[([ xX])\]\s+(T\d{3})(?:\s+\[P\])?\s*(?:\[(US[1-4])\])?\s*(.+)$` as CSM specification activity elements. The checkbox state `[x]`/`[X]` → `activity_status: completed`, `[ ]` → `activity_status: open`. The task ID (TNNN), parallel marker `[P]`, and user story reference `[USN]` are stored as metadata.
- **FR-014**: The OpenSpec specialist rule pack MUST extract requirements and business rules from `### Requirement: <Title> (<optional-ID>)` headings — the `<Title>` becomes a semantic element with `semantic_type: fact`; when an ID like `(FS201)` or `(DC301)` is present it creates a data_group reference.
- **FR-015**: The OpenSpec specialist rule pack MUST extract `O sistema DEVE <action>` and `O sistema NÃO DEVE <action>` statements from requirement bodies as individual business rule elements with `semantic_type: fact` and confidence 0.95. This includes variations: `<Entity> DEVE <action>`, `<Entity> DEVEM <action>`, `<Entity> NÃO DEVE <action>`.
- **FR-016**: The OpenSpec specialist rule pack MUST extract English equivalents — `The system SHALL <action>`, `The system SHALL NOT <action>`, `<Component> SHALL <action>`, `SHOULD <action>`, `MAY <action>` — as `semantic_type: fact` with confidence 0.90.
- **FR-017**: The OpenSpec specialist rule pack MUST extract `#### Scenario: <title>` headings as operation elements with `semantic_type: operation` and confidence 0.95. The scenario title becomes the operation name.
- **FR-018**: The OpenSpec specialist rule pack MUST extract `- **GIVEN** <condition>` lines as precondition facts with `semantic_type: fact` and confidence 0.90. `- **AND** <condition>` following a GIVEN is appended as additional precondition context.
- **FR-019**: The OpenSpec specialist rule pack MUST extract `- **WHEN** <action>` lines as operation triggers with `semantic_type: operation` and confidence 0.95. Variable assignment patterns like `WHEN MaxPric = 80, MinPric = 70` are extracted as data constraints; user action patterns like `WHEN o usuário clica no botão` are extracted as actor-triggered operations.
- **FR-020**: The OpenSpec specialist rule pack MUST extract `- **THEN** <expected>` lines as business rule assertions with `semantic_type: fact` and confidence 0.90. Calculations like `THEN CLV DEVE ser 0` are extracted with the full formula as content.
- **FR-021**: The OpenSpec specialist rule pack MUST extract capability ID patterns — `FS###`, `DC###`, `DR###`, `DT###`, `DP###`, `IC###`, `LC###`, `REQ-*` — as data group references with `semantic_type: entity` and confidence 0.85. Each unique ID creates a data_group entry.
- **FR-022**: The OpenSpec specialist rule pack MUST extract decisions from `### Decision <N>: <Title>` (colon separator) and `### <N>. <Title>` (dot separator) headings in `design.md` files as CSM Decision elements. The heading title becomes the decision description; paragraph content below becomes the rationale. `**Rationale**:`, `**Alternative considered**:` (English), and `**Alternativa considerada:**` (Portuguese) labels are parsed as structured fields when present.
- **FR-023**: The OpenSpec specialist rule pack MUST extract risks and trade-offs from lines matching `- [Risk] <description> → Mitigation: <action>` and `- [Trade-off] <description> → Acceptable because <reason>` as CSM Risk elements. The description becomes the risk text; mitigation/reason becomes structured metadata.
- **FR-024**: The OpenSpec specialist rule pack MUST extract `## Why`, `## What Changes`, `## Context`, and `## Goals / Non-Goals` section content from proposal.md and design.md files as CSM assumption and constraint elements. `Why` and `Context` paragraphs produce assumptions; `Non-Goals` list items produce constraints.
- **FR-025**: The OpenSpec specialist rule pack MUST extract `## Capabilities` sub-sections from proposal.md — `### New Capabilities` items as functional process definitions and `### Modified Capabilities` items as CSM decision elements with change provenance.
- **FR-026**: The OpenSpec specialist rule pack MUST extract `## <N>. <Category>` headings and `- [ ] <N.N> <description>` / `- [x] <N.N> <description>` checklist items from `tasks.md` files as CSM specification activity elements. Completed items (`[x]`) have `activity_status: completed`; pending items (`[ ]`) have `activity_status: open`.
- **FR-027**: The OpenSpec specialist rule pack MUST extract domain entity names — identified by TitleCase words followed by `(` or appearing in code blocks — as CFM data group elements with `semantic_type: entity`. Known entities discovered from real specs include: TradeDay, AggregatedMetrics, DominanceClassification, ConvictionClassification, MoneyFlowClassification, InstitutionalClassification, LiquidityClassification, Diagnosis, TickerList, OrientationPanel, PriceRangePanel.
- **FR-028**: The OpenSpec specialist rule pack MUST extract `## Purpose` section content from master specs as functional process descriptions with `semantic_type: entity` and confidence 0.90.
- **FR-029**: The OpenSpec specialist rule pack MUST extract inline actor references — Portuguese role nouns (Usuário, Sistema, Cliente, Analista, Operador) and English equivalents (User, System, Client, Analyst, Operator) — from requirement text as CFM Actor elements with `semantic_type: entity` and confidence 0.80.
- **FR-030**: Both specialist rule packs MUST assign confidence scores following the RFC-031 table: explicit heading match (1.00), framework convention (0.95), structural heuristic (0.85), pattern inference (0.70).
- **FR-031**: Both specialist rule packs MUST produce elements with deterministic content-hash IDs using the canonical scheme: `sha256(f"{document_id}::{section_id}::{text}")[:16]`.
- **FR-032**: Both specialist rule packs MUST be auto-detected and loaded based on `document.document_type` metadata, extending the existing `_load_framework_packs()` mechanism.
- **FR-033**: Specialist rule packs MUST NOT replace or require modification of the default rule pack — they are additive framework-specific extensions.
- **FR-034**: The deterministic engine MUST continue to function when no specialist rule pack is available for a given document type, falling back to generic rules only.
- **FR-035**: Individual rule extraction failures (regex exceptions, malformed matches) MUST NOT abort the full extraction run — the engine MUST catch, log, and skip the failing rule, then continue processing remaining rules for the same document.
- **FR-036**: Each specialist rule pack YAML file MUST include a `version` metadata field following semantic versioning (`major.minor.patch`). The engine MUST log a warning when loading a rule pack with a major version mismatch against the expected engine compatibility range.
- **FR-037**: The deterministic engine MUST expose a per-document extraction success rate metric (rules executed successfully / rules attempted) as a counter. A per-document rate below 99% MUST be logged at WARN level with the failing document ID and failing rule IDs.

### Design Decisions

- **Regex-based over AST-parsing**: Regex extraction was chosen over full Markdown AST parsing because (a) Speckit and OpenSpec documents follow consistent template patterns where regex targeting section headings and keyword markers captures sufficient semantic content, (b) regex rules are externalizable as YAML (FR-030: Rule Externalization principle), enabling customization without engine code changes, and (c) the deterministic engine already handles confidence scoring to filter low-quality matches. AST parsing would provide more structural precision but would require a parser per Markdown dialect and prevent external rule customization.

### Out of Scope

- LLM hybrid/assisted extraction mode — this feature is purely deterministic; any future LLM integration would be a separate feature.
- User-defined/custom rule pack authoring — all specialist rule packs are built-in and versioned with the codebase.

### Key Entities _(include if feature involves data)_

- **Speckit Specialist Rule Pack**: A YAML rule pack file (`speckit_rules.yaml`) containing regex-based extraction rules tailored to the SpecKit file format conventions — Feature workspaces under `specs/`, artifact types (spec.md, plan.md, tasks.md, research.md, data-model.md, checklist), and common section patterns. Includes a `version` metadata field using semantic versioning.
- **OpenSpec Specialist Rule Pack**: A YAML rule pack file (`openspec_rules.yaml`) containing regex-based extraction rules tailored to the OpenSpec file format conventions — Domain specs under `openspec/specs/`, change artifacts (proposal.md, design.md, tasks.md, delta specs), and common section patterns. Regex patterns cover: Requirement headings (`### Requirement: <Title> (ID)`), DEVE/SHALL statements, Scenario/GIVEN/WHEN/THEN blocks, capability IDs (`FS###`, `DC###`), Decision records, Risk/Trade-off markers, and task checklists. Includes a `version` metadata field using semantic versioning.
- **SpecializedDeterministicFallback**: The combined extraction approach where the DeterministicSemanticEngine loads framework-specific rule packs with rich regex patterns, enabling full end-to-end pipeline execution without any LLM dependency.
- **EvidenceReference**: The provenance record attached to every extracted element — document ID, section ID, text fragment, and originating rule ID. Already defined in the canonical model; specialist rules populate it fully.
- **Discovered Domain Entities (OpenSpec from tests/openspec/)**: Concrete entities extracted from analyzing 29 real OpenSpec domain specs and change artifacts in `tests/openspec/` — TradeDay, AggregatedMetrics, DominanceClassification, ConvictionClassification, MoneyFlowClassification, InstitutionalClassification, LiquidityClassification, DirectionDiagnosis, MoneyFlowDiagnosis, ConvictionDiagnosis, InstitutionalDiagnosis, LiquidityDiagnosis, Diagnosis, TickerList, OrientationPanel, PriceRangePanel, FinancialFlowPanel, DominanceTimelineChart, DiagnosisPanel, ClassificationBar, CLVGauge, BuySellBar, PriceRangeDiagram, IndicatorEngine, B3Client, B3DataRepository, CacheManager, AnalyzeTickersUseCase, FlowScopeGUI, EfficiencyClassification, EfficiencyPanel, ParticipationPanel, IndexCache, ChartEmptyState, GetDownloadPortfolioDay, B3Index, TradeInformationConsolidated, DailyEfficiencyStrategy.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Running `specmetrics measure` on a SpecKit repository with 5 feature workspaces completes all pipeline stages and produces non-empty CFM (at least 10 elements across all categories) and non-empty CSM (at least 5 elements across all categories) — no LLM required.
- **SC-002**: Running `specmetrics measure --repo tests/openspec/` on the OpenSpec examples (29 domain specs, 3 active changes, 38 archived changes) completes all pipeline stages in ≤ 30s and produces CFM with at least 15 elements (across actors, business_rules, data_groups, operations) and CSM with at least 8 elements (across decisions, risks, assumptions, specification_activities) — no LLM required.
- **SC-003**: All 8 measurement plugins (FPA, SFP, SNAP, Token Points, Cognitive Points, Story Points, T-Shirt, BCP) produce non-zero results from deterministic-only extraction on a repository with representative specification content.
- **SC-004**: Processing the same document set twice with the same specialist rule packs produces byte-identical extraction output (excluding `duration_ms`).
- **SC-005**: The speckit specialist rule pack extracts at least 20 elements from `007-canonical-functional-model/spec.md` (118 lines, a representative spec with all standard sections), including: 2 user story headings → CFM functional processes, 5+ numbered Given/When/Then scenarios → precondition/action/assertion facts, 9 FR-NNN requirements → business rules, 7 Key Entities → actors/data groups, 6 SC-NNN success criteria → acceptance criteria, 3+ assumption lines, 3+ edge case questions → open questions, 1 engaged principles list → constraints.
- **SC-006**: The openspec specialist rule pack extracts at least 25 elements from `tests/openspec/specs/ticker-analysis/spec.md` (209 lines, the largest Portuguese spec), including: 8+ business rules from `O sistema DEVE`/`DEVE` statements, 6+ operations from `#### Scenario:` blocks, 8+ precondition/action facts from GIVEN/WHEN/THEN lists, 3+ actors from inline role references (Usuário, Sistema, Analista), 2+ data groups from entity names (CLVGauge, ClassificationBar, PriceRangeDiagram, BuySellBar).
- **SC-007**: The openspec specialist rule pack extracts at least 3 decisions from `tests/openspec/changes/diagnosis-panel/design.md` (which contains 5 explicit `### Decision` sections with Rationale and Alternative considered fields) and also recognizes `### <N>. <Title>` dot-separator format from `tests/openspec/changes/eficiencia-do-movimento/design.md` (6 decisions) and `tests/openspec/changes/participation-negociacoes/design.md` (7 decisions) — total of 18+ decision elements across all design.md files.
- **SC-008**: The openspec specialist rule pack extracts at least 60 elements total from processing all 29 master specs in `tests/openspec/specs/` (domains: flow-indicators, dominance-classifiers, price-range-indicators, ticker-analysis, gui-interface, dag-engine, data-ingestion, and 22 more), including DEVE/SHALL business rules, Scenario/WHEN operations, GIVEN preconditions, THEN assertions, capability IDs (FS###, DC###, DR###, etc.), and inline actor references. Additionally, extracts at least 30 elements from the 3 active changes' proposal/design/tasks/delta files combined.

## Assumptions

- The existing DeterministicSemanticEngine infrastructure (Markdown parsing, visitor pattern, rule engine, evidence reference generation, content-hash ID scheme) is stable and available.
- The CFM and CSM classifiers already handle the semantic_types and content patterns that the specialist rules produce — no changes to classifier logic are needed.
- Specialist rule packs are stored as YAML files under `specmetrics/kernel/rules/` and follow the existing `ExtractionRule` schema.
- Framework auto-detection via `document.document_type` in `_load_framework_packs()` is sufficient — no changes to adapter metadata are needed.
- The specification templates (OpenSpec and SpecKit) that users follow produce section headings and content patterns consistent with the extraction regexes. For non-standard documents, generic rules provide baseline coverage.
- All 8 measurement plugins depend on CFM (and optionally CSM) but do not require specific minimum element thresholds — they gracefully handle empty or sparse models.
- The Speckit format analysis was performed on the specmetrics project itself (29 features, ~200 files). Other Speckit repositories may have different conventions; the specialist rules cover the most common patterns (User Story headings, numbered GIVEN/WHEN/THEN, FR-NNN/SC-NNN requirements, Key Entities, Assumptions sections) while generic rules provide baseline coverage.
- The Speckit specialist rules expect spec.md files following the standard template (spec-template.md). Features that deviate from the template or use custom section structures still receive generic rule coverage.
- Not all Speckit features have the complete set of optional files (plan.md, tasks.md, data-model.md, research.md, quickstart.md, contracts/). Rules for optional artifacts gracefully produce zero elements when the files are absent.
- The OpenSpec format analysis was performed on the examples in `tests/openspec/` (29 domains, 41 changes total). Other OpenSpec repositories may follow different conventions; the specialist rules cover the most common patterns (Requirement/Scenario/DEVE/SHALL/GIVEN/WHEN/THEN) while generic rules handle unknown structures.
- OpenSpec specs in Portuguese use `DEVE`/`DEVEM`/`NÃO DEVE` as mandatory keywords; English specs use `SHALL`/`SHALL NOT`. Both patterns are supported by the specialist rules with appropriate confidence scores.
- The `document_type` metadata produced by the OpenSpec adapter accurately identifies artifact types (specification, proposal, design, tasks) — this is required for the specialist rules to apply document-specific extraction strategies.
- Delta specs (`## ADDED Requirements` vs `## MODIFIED Requirements`) are distinguished by heading text content — the existing heading-matching mechanism in the deterministic engine supports this without structural changes. The flat `.spec.delta.md` format uses `## Modified Requirements` (without "ADDED" section) and `(substitui "...")` parenthetical markers for modified requirements.
- No-change spec variants (`specs/spec.md`, `_index.md`, `README.md`) contain fixed strings like `"No specification changes required"` — the specialist rules should detect these and skip extraction to avoid false positive elements.
- The CFM classifier's `ACTOR_PATTERNS` regex already matches Portuguese role suffixes (`-or`, `-ista`, etc.) — new patterns like `Usuário`, `Sistema`, `Cliente`, `Analista`, `Operador` may need to be added to the actor dictionary for correct classification.
- Decision records use two heading formats: `### Decision <N>: <Title>` (English, colon separator) and `### <N>. <Title>` (Portuguese, dot separator). The specialist rules must support both formats and their respective rationale field labels (`**Alternative considered:**` English, `**Alternativa considerada:**` Portuguese).
