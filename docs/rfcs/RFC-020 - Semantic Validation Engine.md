# RFC-020 — Semantic Validation Engine

**Release:** 0.2 – Knowledge Layer

**Status:** Draft

**Authors:** SpecMetrics Project

**Target Version:** 0.2

---

# 1. Summary

This RFC introduces the **Semantic Validation Engine**, a deterministic validation subsystem responsible for assessing the quality, consistency and completeness of the **Canonical Functional Model (CFM)** before downstream consumers—such as measurement engines, exporters or AI agents—use it.

Unlike syntax validation or document linting, the Semantic Validation Engine operates exclusively on the Canonical Functional Model, ensuring that validation remains independent from Specification Driven Development frameworks and semantic extraction providers.

The engine produces structured diagnostics rather than modifying the model itself, allowing organizations to define quality gates appropriate to their governance policies.

---

# 2. Motivation

Release 0.1 guarantees deterministic measurement, but assumes that the generated CFM is semantically valid.

In practice, semantic extraction may produce:

- duplicated concepts;
- incomplete business processes;
- orphan entities;
- ambiguous relationships;
- unsupported evidence;
- inconsistent business rules.

Without validation, these issues propagate into measurement engines and external integrations, reducing confidence in the generated engineering assets.

The Semantic Validation Engine establishes the first formal quality gate of the Knowledge Layer.

---

# 3. Goals

The Semantic Validation Engine shall:

- validate semantic consistency;
- validate evidence integrity;
- detect ambiguous knowledge;
- classify diagnostics by severity;
- produce deterministic results;
- support organization-specific validation rules;
- remain independent from measurement methodologies.

---

# 4. Non Goals

This RFC does not include:

- Markdown linting;
- OpenSpec validation;
- SpecKit validation;
- grammar checking;
- spelling correction;
- AI rewriting;
- automatic repair of semantic models.

The engine reports problems.

It never modifies the Canonical Functional Model.

---

# 5. Architectural Position

```text
Specifications

↓

Semantic Extraction

↓

Evidence Graph

↓

Canonical Functional Model

↓

Semantic Validation Engine

↓

Validated CFM

↓

Measurement Engine

↓

Exporters
```

Validation becomes mandatory before deterministic measurement.

---

# 6. Design Principles

The engine follows existing platform principles.

## Semantic Before Structural

Validation operates exclusively on semantic concepts.

Never on Markdown.

---

## Evidence First

Every diagnostic must reference the evidence that originated it.

---

## Deterministic

Given the same CFM,

the same Rule Pack,

the same Validation Pack,

the engine shall always generate identical diagnostics.

---

## Read Only

Validation never mutates the CFM.

---

## Plugin-Oriented

Validation rules are extensible through plugins.

---

# 7. Validation Categories

The engine organizes diagnostics into categories.

---

## 7.1 Structural Integrity

Examples

- duplicated IDs
- missing references
- broken relationships
- cyclic dependencies

---

## 7.2 Semantic Integrity

Examples

- duplicated actors
- duplicated entities
- duplicated functional processes
- contradictory business rules
- conflicting operations

---

## 7.3 Completeness

Examples

Functional Process without:

- actor
- operation
- entity
- evidence

Business Rule without evidence.

Relationship without endpoints.

---

## 7.4 Evidence Integrity

Examples

- missing evidence
- invalid document reference
- orphan evidence
- confidence below threshold

---

## 7.5 Consistency

Examples

Entity exists

↓

no process manipulates it

Actor exists

↓

never performs any operation

Operation exists

↓

no target entity

---

## 7.6 Organizational Rules

Validation Packs may define rules such as

```yaml
customer:
  must_have:
    - create
    - update

invoice:
  requires:
    - approval
```

---

# 8. Diagnostic Severity

Four severity levels are defined.

## INFO

Informational observations.

Does not affect measurement.

---

## WARNING

Possible semantic issue.

Measurement may continue.

---

## ERROR

Likely semantic inconsistency.

Measurement should continue only if configured.

---

## CRITICAL

The CFM is considered invalid.

Pipeline execution stops.

---

# 9. Diagnostic Model

Each diagnostic contains

```yaml
id:

category:

severity:

code:

message:

concept:

location:

evidence:

recommendation:
```

Example

```yaml
id: VAL-0045

category: Completeness

severity: ERROR

code: PROCESS_WITHOUT_ACTOR

message: Functional Process has no Actor.

concept: Register Customer

evidence: requirements.md#142

recommendation: Associate an Actor.
```

---

# 10. Validation Packs

Validation logic is externalized.

```
validation/

    default/

    banking/

    government/

    healthcare/
```

Validation Packs may define

- mandatory concepts
- forbidden concepts
- naming conventions
- minimum evidence confidence
- organizational constraints

---

# 11. Execution Model

Pipeline event

```
CanonicalModelBuilt
```

↓

Semantic Validation Engine

↓

ValidationCompleted

↓

Pipeline continues

or

PipelineFailed

---

# 12. CLI

New command

```bash
specmetrics validate
```

Options

```bash
specmetrics validate

specmetrics validate --strict

specmetrics validate --json

specmetrics validate --markdown

specmetrics validate --validation-pack banking
```

---

# 13. MCP

New tools

```
Validate Knowledge

List Diagnostics

Explain Diagnostic

Validation Summary
```

---

# 14. Outputs

Supported formats

- JSON
- Markdown
- SARIF (future)
- HTML (future)

---

# 15. Validation Report

Example

```text
Semantic Validation Report

Status

PASS

Diagnostics

INFO

3

WARNING

5

ERROR

1

CRITICAL

0

Health Score

94%

Validated Concepts

Actors

12

Entities

18

Processes

31

Rules

22
```

---

# 16. Health Score

The engine calculates an overall semantic quality score.

```
100

↓

warnings

↓

errors

↓

critical
```

Example

```
Semantic Health

96%

Evidence Coverage

98%

Relationship Coverage

100%

Completeness

94%

Consistency

97%
```

The score is informational only.

Pipeline decisions are based on severity.

---

# 17. Public Events

```text
ValidationStarted

ValidationCompleted

ValidationFailed
```

---

# 18. Plugin Interface

```python
class ValidationPlugin:

    validate(
        cfm,
        validation_pack
    ) -> ValidationResult
```

Multiple validators may execute sequentially.

---

# 19. Quality Gates

Projects may define

```yaml
quality_gate:
  max_warning: 10

  max_error: 0

  max_critical: 0

  minimum_health: 90
```

If violated

```
PipelineFailed
```

is emitted.

---

# 20. Future Evolution

The Semantic Validation Engine establishes the first quality gate of the Knowledge Layer and provides the foundation for more advanced semantic governance capabilities. Future releases may extend this subsystem with:

- semantic anti-pattern detection;
- AI-assisted repair suggestions;
- semantic drift detection;
- architecture conformance validation;
- business glossary compliance;
- domain-driven design heuristics;
- regulatory and compliance validation packs;
- cross-project semantic consistency analysis.

By validating the Canonical Functional Model instead of source specifications, the engine remains aligned with the architectural principles of SpecMetrics, preserving framework independence, deterministic behavior and long-term extensibility.
