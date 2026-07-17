# Feature Specification: Measurement Engine Plugin — Story Points (Modified Fibonacci)

**Feature Branch**: `024-measurement-engine-storypoints`

**Created**: 2026-07-17

---

## Clarifications

### Session 2026-07-17

- **Q:** Which Story Point scale SHALL be supported by the default implementation? → **A:** Modified Fibonacci (1, 2, 3, 5, 8, 13, 20, 40, 100).
- **Q:** Are Story Points intended to replace Cognitive Points? → **A:** No. Story Points represent relative implementation effort, while Cognitive Points measure cognitive complexity.
- **Q:** Can organizations customize estimation heuristics? → **A:** Yes, through Rule Packs.
- **Q:** Does the plugin attempt to emulate Planning Poker? → **A:** No. The plugin performs deterministic estimation based on the Canonical Functional Model.
- **Q:** How should raw effort scores be calculated per Functional Process? → **A:** Multi-factor weighted sum: each configurable factor (business interactions, data, integrations, rules, workflow, exceptions) scored independently, multiplied by configurable coefficient, then summed per work item.
- **Q:** What attributes should FunctionalWorkItem, RawEffortScore, StoryPointEstimate, and MeasurementEvidence have? → **A:** Each work item carries element_id, element_name, raw_score, normalized_value, factor_breakdown, evidence_refs, and applied_rules — consistent with 022/023 patterns.

---

## Status

Draft

**Input:** User description: "F24"

---

# Overview

The Story Points Measurement Engine is a deterministic SpecMetrics plugin responsible for estimating the relative implementation effort of functional work items using the **Modified Fibonacci** scale.

Unlike traditional agile estimation sessions that rely on Planning Poker and team consensus, this plugin derives repeatable Story Point estimates directly from the Canonical Functional Model (CFM) using configurable organizational heuristics.

The objective is **not** to replace human estimation, but to provide a consistent baseline suitable for portfolio analysis, forecasting, benchmarking and historical comparisons.

The plugin performs no semantic inference and relies exclusively on the validated Canonical Functional Model.

---

# Objectives

The Measurement Engine SHALL:

- produce deterministic Story Point estimates;
- normalize estimates to the Modified Fibonacci sequence;
- preserve complete explainability;
- support organizational Rule Packs;
- integrate with the Measurement Plugin infrastructure;
- enable reproducible effort baselines across projects.

---

# User Scenarios & Testing

## User Story 1 — Automatic Story Point Estimation (Priority: P1)

A project manager executes:

```bash
specmetrics measure --method storypoints
```

The engine estimates Story Points for every functional work item contained in the Canonical Functional Model.

### Acceptance

- estimation completes automatically;
- every estimated item appears in the report;
- repeated executions produce identical results.

---

## User Story 2 — Explainable Estimation (Priority: P1)

A reviewer wants to understand why a backlog item received **8 Story Points**.

The engine exposes:

- originating CFM elements;
- applied estimation rules;
- normalized Fibonacci value;
- evidence supporting the estimate.

---

## User Story 3 — Organizational Calibration (Priority: P2)

A company wishes to assign higher effort to integrations.

A Rule Pack adjusts weighting rules.

The plugin applies the custom policy before normalization.

---

## User Story 4 — Pipeline Integration (Priority: P2)

The plugin is automatically discovered and executed after Rule Pack processing.

---

# Edge Cases

- Empty CFM
- Missing Functional Processes
- Duplicate functional items
- Invalid Rule Pack
- Cyclic references
- Extremely large CFMs
- Functional item producing score above maximum supported scale
- Functional item producing score below minimum supported scale

---

# Constitution Check

## Principle IV — Deterministic Execution

Satisfied.

No AI participates in estimation.

---

## Principle VI — Explainability

Satisfied.

Every estimated Story Point value is fully traceable.

---

## Principle VII — Canonical Representation

Satisfied.

Only the Canonical Functional Model is consumed.

---

## Principle VIII — Plugin Architecture

Satisfied.

Plugin is discovered through Entry Points.

---

## Principle IX — Rule Externalization

Satisfied.

Organizational heuristics are externalized.

---

# Functional Requirements

## General

### FR-001

The Measurement Engine SHALL consume only the Canonical Functional Model.

---

### FR-002

The engine SHALL execute without LLM assistance.

---

### FR-003

The engine SHALL produce deterministic Story Point estimates.

---

### FR-004

The engine SHALL preserve evidence references.

---

### FR-005

The engine SHALL support organizational Rule Packs.

---

### FR-006

The engine SHALL expose machine-readable output.

---

### FR-007

The engine SHALL execute as a discoverable Measurement Plugin.

---

### FR-008

The engine SHALL support incremental execution.

---

### FR-009

The engine SHALL support pipeline execution.

---

### FR-010

The engine SHALL complete estimation even when warnings are generated.

---

# Estimation Model

Story Points estimate the **relative effort required to implement a functional work item**.

The plugin SHALL estimate effort from the characteristics already represented in the Canonical Functional Model.

Each measurable Functional Process becomes one estimable work item.

---

# Functional Identification

### FR-011

The engine SHALL identify Functional Processes through CFM node type and semantic attributes.

---

### FR-012

Each Functional Process SHALL represent one estimable backlog item.

---

### FR-013

Implementation details SHALL NOT directly influence estimation unless defined by Rule Packs.

---

### FR-014

Duplicate Functional Processes SHALL be merged using the CFM node ID and content fingerprint (SHA-256 of `document_id`, `section_id`, `text`, `semantic_type`).

---

# Estimation Rules

### FR-015

The engine SHALL compute a raw effort score for each Functional Process using deterministic rules.

---

### FR-016

The raw effort score SHALL be calculated as a multi-factor weighted sum:

```
raw_score = Σ(factor_score × factor_coefficient) over configured factors
```

Each factor scored independently per Functional Process.

---

### FR-016a

The engine SHALL provide default factors and coefficients derived from CFM element characteristics. Organizations MAY redefine factors, scores, and coefficients through Rule Packs.

---

### FR-016b

Default factors SHALL include:

- **business interactions**: Count of related actors and external entities
- **logical information**: Count of related data groups and operations
- **external integrations**: Count of relationships with external data groups
- **business rule density**: Count of associated business rules
- **workflow breadth**: Number of operations and sub-processes
- **exception handling**: Presence of conditional or branching logic

### FR-017

The default estimation model SHALL remain deterministic.

---

### FR-018

Raw effort scores SHALL be normalized to the nearest Modified Fibonacci value.

---

### FR-019

The default Modified Fibonacci sequence SHALL be:

```
1
2
3
5
8
13
20
40
100
```

---

### FR-020

The engine SHALL NEVER generate Story Point values outside the configured scale.

---

### FR-021

Organizations MAY replace the normalization table through Rule Packs.

---

### FR-022

The normalization process SHALL be deterministic.

---

# Rule Packs

### FR-023

Rule Packs MAY redefine weighting coefficients.

---

### FR-024

Rule Packs MAY redefine normalization thresholds.

---

### FR-025

Rule Packs SHALL NOT alter deterministic execution.

---

### FR-026

All Rule Pack adjustments SHALL be reported.

---

# Explainability

### FR-027

Every estimated work item SHALL expose:

- originating CFM node;
- originating specification;
- applied rules;
- raw effort score;
- normalized Story Point value.

---

### FR-028

Evidence SHALL be immutable.

---

### FR-029

Evidence SHALL survive export.

---

# Pipeline

### FR-030

Pipeline execution order SHALL be:

```text
Semantic Extraction

↓

Canonical Functional Model

↓

Rule Pack Engine

↓

Story Points Measurement Engine

↓

Export Layer
```

---

### FR-031

The Measurement Engine SHALL emit Measurement Events.

---

### FR-032

The plugin SHALL support asynchronous execution.

---

### FR-033

The plugin SHALL support incremental recomputation.

---

### FR-034

Only modified Functional Processes SHALL be re-estimated.

---

# Measurement Result

The output SHALL include:

```text
Measurement Method

Version

Measurement Timestamp

Estimated Work Items

Raw Effort Scores

Story Point Distribution

Total Story Points

Applied Rule Packs

Evidence References

Warnings

Execution Statistics
```

---

# Key Entities

## Story Point Measurement Result

Complete estimation output identified by pipeline run ID.

Contains:
- **method**: "StoryPoints"
- **scale**: "ModifiedFibonacci"
- **estimated_items**: List of FunctionalWorkItem
- **total_story_points**: Sum of all normalized values
- **distribution**: Count of work items per Fibonacci value
- **applied_rule_pack**: Rule Pack identifier
- **warnings**: List of non-fatal issues
- **execution_metadata**: Timing, counts, version

---

## FunctionalWorkItem

A Functional Process eligible for Story Point estimation.

Contains:
- **element_id**: UUID of the originating Functional Process
- **element_name**: Human-readable name
- **raw_score**: Pre-normalization raw effort score (float)
- **normalized_value**: Final Story Point value from Fibonacci scale
- **factor_breakdown**: Per-factor scores (dict of factor_name → score)
- **applied_rules**: Rules and coefficients applied to this item
- **evidence_refs**: Provenance links to CFM elements

---

## RawEffortScore

Intermediate deterministic score before normalization. Calculated as multi-factor weighted sum per FR-016.

Contains:
- **value**: Total raw effort score (float)
- **factor_breakdown**: Per-factor scores with coefficients applied

---

## StoryPointEstimate

Final Modified Fibonacci value assigned to a FunctionalWorkItem.

Contains:
- **value**: Integer from the configured Fibonacci scale
- **raw_score**: The raw effort score that produced this estimate
- **normalization_rule**: Threshold or rounding rule applied

---

## MeasurementEvidence

References explaining the estimate.

Contains:
- **element_id**: CFM node ID
- **document_id**: Originating document
- **section_id**: Originating section
- **applied_rule**: Rule applied at this step
- **text**: Supporting text excerpt


## Rule Pack

External policy modifying estimation heuristics.

---

# Plugin Interfaces

```text
MeasurementPlugin

measure()

validate()

describe()

supported_methods()

version()
```

---

# Output Example

```json
{
  "method": "StoryPoints",
  "scale": "ModifiedFibonacci",
  "estimated_items": 37,
  "story_points": 196,
  "distribution": {
    "3": 8,
    "5": 12,
    "8": 10,
    "13": 5,
    "20": 2
  },
  "warnings": [],
  "rule_pack": "default",
  "explainability": []
}
```

---

# Observability

### FR-035

The engine SHALL emit structured INFO and ERROR log messages for estimation start, completion and failures.

---

### FR-036

The engine SHALL emit OpenTelemetry metrics including:

- estimation duration histogram;
- estimated work item gauge;
- Story Point distribution histogram.

---

# Success Criteria

## SC-001

Repeated executions SHALL produce identical Story Point estimates.

---

## SC-002

100% of estimated work items SHALL include explainability evidence.

---

## SC-003

Estimation SHALL complete in under five seconds for medium-sized CFMs (≤500 Functional Processes).

---

## SC-004

Incremental execution SHALL re-estimate only modified Functional Processes.

---

## SC-005

Plugin SHALL be automatically discovered.

---

## SC-006

Invalid Rule Packs SHALL not prevent estimation.

---

## SC-007

Large CFMs (>1000 Functional Processes) SHALL scale approximately linearly (≤15% deviation per doubling of Functional Process count).

---

# Non-Goals

The plugin does **not**:

- perform Planning Poker;
- replace team consensus;
- measure cognitive complexity;
- estimate development duration;
- estimate project cost;
- invoke LLMs;
- parse source code;
- perform semantic extraction.

---

# Assumptions

- The Canonical Functional Model has already been validated.
- Rule Packs have been resolved before estimation.
- Export plugins consume Measurement Results.
- The Modified Fibonacci sequence is the default estimation scale.
- Story Points are treated as an independent measurement methodology, separate from SFP, FPA, SNAP, COSMIC and Cognitive Points.

---

# Implementation Notes

The Story Points Measurement Engine provides a deterministic approximation of agile relative estimation by applying configurable organizational heuristics to the Canonical Functional Model and normalizing the resulting effort scores to the Modified Fibonacci sequence. Its purpose is to establish a reproducible baseline for portfolio governance, forecasting and cross-project comparison, while preserving compatibility with traditional team-based estimation practices. The plugin shares the same infrastructure as all SpecMetrics measurement engines—including pipeline integration, Rule Packs, explainability, event contracts and export mechanisms—allowing organizations to compare Story Points alongside other sizing methods using a common canonical representation.

> **Note:** This specification defines the **plugin architecture, deterministic estimation workflow, normalization model, explainability requirements and integration contracts** for Story Point estimation. It intentionally does not attempt to reproduce or replace collaborative agile estimation practices such as Planning Poker, which remain team-driven activities outside the scope of this plugin.
