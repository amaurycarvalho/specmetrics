# RFC-021 — Semantic Diff Engine

**Release:** 0.2 – Knowledge Layer

**Status:** Draft

**Authors:** SpecMetrics Project

**Target Version:** 0.3

---

# 1. Summary

This RFC introduces the **Semantic Diff Engine**, a deterministic comparison engine responsible for identifying semantic differences between two versions of the **Canonical Functional Model (CFM)**.

Unlike textual or structural diff tools, the Semantic Diff Engine compares engineering knowledge rather than document formatting or source code.

Its primary purpose is to detect functional evolution between software specifications while preserving complete traceability to the originating evidence.

The resulting Semantic Diff becomes a reusable engineering artifact that supports impact analysis, functional measurement, governance and AI-assisted engineering workflows.

---

# 2. Motivation

Traditional diff tools compare files.

Version control systems compare text.

Software quality tools compare source code.

None of these approaches identify what actually changed from a business or functional perspective.

For example,

```text
Rename field

↓

Large textual diff

↓

No functional change
```

or

```text
Business rule modified

↓

One-line Markdown change

↓

Major functional impact
```

Organizations need to understand how software functionality evolves over time, independently of document organization or implementation details.

The Semantic Diff Engine addresses this problem by comparing two Canonical Functional Models rather than their source documents.

---

# 3. Goals

The Semantic Diff Engine shall:

- compare two Canonical Functional Models;
- detect semantic additions, removals and modifications;
- classify changes by concept type;
- preserve evidence traceability;
- remain deterministic;
- expose reusable machine-readable diffs;
- support future incremental measurement.

---

# 4. Non Goals

This RFC does not provide:

- Git integration;
- Markdown comparison;
- line-by-line document diff;
- source code diff;
- merge capabilities;
- conflict resolution.

The engine compares semantic knowledge only.

---

# 5. Architectural Position

```text
Specification A
        │
        ▼
CFM A

               Semantic Diff Engine

CFM B
        ▲
        │
Specification B

        │
        ▼

Semantic Diff

        │

Impact Analysis
Measurement
Reports
AI Agents
```

The Semantic Diff Engine consumes only Canonical Functional Models.

---

# 6. Design Principles

## Knowledge First

The engine compares engineering knowledge.

Never documents.

---

## Canonical Independence

The comparison is completely independent from:

- OpenSpec
- SpecKit
- semantic providers
- document structure

---

## Deterministic

Given the same two CFMs,

the engine always produces the same Semantic Diff.

---

## Evidence Preservation

Every detected change references the evidence supporting both versions.

---

## Explainability

Every reported difference must explain:

- what changed;
- where it changed;
- why it is considered a semantic change.

---

# 7. Supported Concept Types

The engine compares every canonical concept.

- Functional Processes
- Business Entities
- Actors
- Operations
- Business Rules
- Data Structures
- Relationships
- Events
- Constraints

Future concepts automatically participate in the comparison.

---

# 8. Change Types

Every detected difference belongs to one of four categories.

---

## Added

Concept exists only in the newer CFM.

Example

```text
Register Supplier
```

---

## Removed

Concept exists only in the previous CFM.

Example

```text
Cancel Subscription
```

---

## Modified

Same concept.

Different semantics.

Examples

- new business rule
- changed relationship
- different actor
- modified operation

---

## Unchanged

Concept preserved without semantic modification.

---

# 9. Change Classification

Each detected change receives a semantic classification.

Examples

```text
NEW_FUNCTION

REMOVED_FUNCTION

UPDATED_RULE

UPDATED_ENTITY

UPDATED_RELATIONSHIP

UPDATED_OPERATION

NEW_ACTOR

REMOVED_EVENT
```

These classifications are stable identifiers consumed by downstream tools.

---

# 10. Impact Levels

Each change receives an estimated impact level.

```text
LOW

MEDIUM

HIGH

CRITICAL
```

Examples

| Change                     | Impact   |
| -------------------------- | -------- |
| Description updated        | LOW      |
| Actor changed              | MEDIUM   |
| Business Rule modified     | HIGH     |
| Functional Process removed | CRITICAL |

Impact calculation is deterministic.

---

# 11. Diff Model

Each change contains

```yaml
id:

change_type:

concept_type:

impact:

concept_id:

old_value:

new_value:

old_evidence:

new_evidence:

explanation:
```

Example

```yaml
id: DIFF-0012

change_type: Modified

concept_type: Business Rule

impact: HIGH

concept_id: BR-004

old_value: Customer may cancel anytime

new_value: Customer may cancel within 30 days

old_evidence: requirements.md#82

new_evidence: requirements.md#104

explanation: Cancellation policy changed.
```

---

# 12. Diff Report

Example

```text
Semantic Diff Report

Compared Models

1.2.0

↓

1.3.0

Summary

Added

4

Modified

8

Removed

1

Unchanged

126

Overall Impact

HIGH
```

---

# 13. Concept-Level Diff

Example

```text
Business Entity

Customer

Status

Modified

Changes

+ Loyalty Category

Evidence

requirements.md

business-rules.md
```

---

# 14. Relationship Diff

Relationships are compared independently.

Examples

```text
Customer

↓

owns

↓

Order
```

becomes

```text
Customer

↓

owns

↓

Subscription
```

Relationship changes are reported explicitly.

---

# 15. Evidence Comparison

Every difference references both evidence sources.

```text
Old Evidence

requirements.md#120

↓

New Evidence

requirements.md#158
```

This enables complete traceability during reviews.

---

# 16. CLI

New command

```bash
specmetrics diff model-a model-b
```

Options

```bash
specmetrics diff old new

specmetrics diff old new --summary

specmetrics diff old new --json

specmetrics diff old new --markdown

specmetrics diff old new --concept BusinessRule

specmetrics diff old new --impact HIGH
```

---

# 17. MCP

New tools

```text
Compare Specifications

Semantic Diff

Explain Difference

List Changed Concepts

Impact Summary
```

---

# 18. Outputs

Supported formats

- JSON
- Markdown
- HTML (future)
- GraphML (future)

---

# 19. Downstream Consumers

The Semantic Diff becomes an engineering artifact consumed by:

- Measurement Engine
- Incremental Pipeline
- Validation Engine
- AI Agents
- Export Plugins
- Future Dashboards

The diff is not merely a report.

It is reusable semantic knowledge.

---

# 20. Public Events

```text
SemanticDiffStarted

SemanticDiffCompleted

SemanticDiffGenerated
```

---

# 21. Plugin Interface

```python
class SemanticDiffPlugin:

    compare(
        previous_cfm,
        current_cfm
    ) -> SemanticDiff
```

Alternative comparison strategies may be implemented without modifying the platform core.

---

# 22. Incremental Measurement Support

Although the Semantic Diff Engine does not perform functional measurement, its output provides the semantic foundation for future incremental measurement methodologies.

Measurement plugins may consume Semantic Diff artifacts to:

- identify impacted Functional Processes;
- avoid reprocessing unchanged concepts;
- support incremental Function Point Analysis;
- optimize deterministic measurement execution.

The Semantic Diff Engine itself remains methodology-independent.

---

# 23. Future Evolution

The Semantic Diff Engine establishes semantic evolution as a first-class engineering capability within SpecMetrics. Future releases may extend this subsystem with:

- semantic timeline visualization;
- architectural evolution analysis;
- semantic drift detection;
- impact propagation graphs;
- release comparison dashboards;
- AI-generated change summaries;
- automatic release notes based on semantic changes;
- integration with version control systems;
- change risk prediction;
- semantic merge assistance.

By comparing Canonical Functional Models instead of documents or source code, the Semantic Diff Engine reinforces the Knowledge Layer vision of SpecMetrics, where software evolution is understood in terms of business semantics rather than textual modifications. This capability also serves as the architectural foundation for the Incremental Pipeline (RFC-023), making it one of the key enabling technologies for subsequent platform evolution.
