# RFC-029 — Cognitive Points Measurement Engine

**Status:** Draft

**Authors:** SpecMetrics Project

**Created:** 2026-07-17

**Target Release:** 0.3 – AI Engineering Metrics

---

# Abstract

This RFC introduces **Cognitive Points (CP)**, a deterministic measurement methodology for estimating the expected **human cognitive effort** required during AI-assisted software engineering.

As Large Language Models increasingly automate software implementation, the primary human bottleneck shifts from writing code to understanding requirements, refining specifications, reviewing generated artifacts, validating business behavior, and approving delivery.

Cognitive Points measure this Human-in-the-Loop (HITL) effort.

The methodology combines the **Canonical Specification Model (CSM)** and the **Canonical Functional Model (CFM)** with a configurable cognitive model inspired by **Bloom's Taxonomy**, producing a normalized engineering metric suitable for planning, forecasting, and engineering governance.

---

# Motivation

Software engineering has historically estimated human effort by assuming that developers spend most of their time implementing software.

That assumption is rapidly changing.

Modern AI-assisted workflows increasingly automate:

- code generation
- documentation generation
- unit test generation
- refactoring
- boilerplate implementation

Consequently, the limiting resource is no longer code production.

It becomes human cognition.

Engineers now spend proportionally more time:

- understanding complex domains
- resolving ambiguities
- reviewing specifications
- validating generated code
- confirming business correctness
- making architectural decisions
- approving production readiness

Organizations currently have no deterministic methodology to estimate this cognitive workload before implementation begins.

---

# Problem Statement

Traditional estimation techniques answer different questions.

Function Points answer:

> How much software is being delivered?

Story Points answer:

> How much implementation effort does the team perceive?

Neither answers:

- How much human review will be required?
- How cognitively demanding is this specification?
- How much validation effort will AI-generated software require?
- How much review capacity must the team reserve?
- Which backlog items are most cognitively expensive?

As AI assumes implementation responsibilities, these questions become central to engineering planning.

---

# Goals

Cognitive Points aim to provide:

- deterministic cognitive estimation
- framework-independent measurement
- explainable calculations
- configurable organizational calibration
- planning support for Human-in-the-Loop activities
- review capacity forecasting
- specification quality awareness

The metric is intended to support:

- Sprint Planning
- Kanban replenishment
- PI/IP Planning
- Portfolio Planning
- Engineering governance
- Review capacity management
- AI-assisted delivery planning

---

# Non-Goals

Cognitive Points do **not** attempt to:

- measure elapsed review time
- evaluate developer productivity
- replace Story Points
- estimate implementation duration
- assess individual performance
- measure software quality

Cognitive Points estimate expected cognitive workload—not productivity, velocity, or execution time.

---

# Conceptual Model

Cognitive Points estimate the human intellectual effort required throughout the software delivery lifecycle.

The engine combines two canonical models.

```text
Repository
        │
        ▼
Evidence Graph
        │
        ├────────────┐
        ▼            ▼
      CFM           CSM
        │            │
        └─────┬──────┘
              ▼
   Cognitive Points Engine
```

---

# Measurement Model

The measurement is composed of two independent dimensions.

```text
Cognitive Points

=

Specification Review Effort

+

Functional Validation Effort
```

---

## Specification Review Effort

Derived exclusively from the Canonical Specification Model.

Represents the cognitive effort required to:

- explore requirements
- clarify ambiguities
- refine specifications
- evaluate assumptions
- validate constraints
- assess risks
- review acceptance criteria

This dimension captures the intellectual work required **before implementation**.

---

## Functional Validation Effort

Derived exclusively from the Canonical Functional Model.

Represents the cognitive effort required to verify that generated software correctly implements the specified behavior.

Examples include reviewing:

- functional processes
- business rules
- state transitions
- operations
- data relationships
- domain interactions

This dimension captures the intellectual work required **after implementation**.

---

# Content-Based Estimation (v2)

Cognitive Points v2 introduces content-based estimation, enhancing the Bloom taxonomy classification with a formula that accounts for the actual text volume and sub-type differentiation of each specification element.

## Scoring Formula

```
score = bloom_weight + (content_tokens × content_multiplier)
```

Where:
- **bloom_weight**: The element's Bloom taxonomy weight (1.0–8.0) from the calibration profile, determined by element type and optional sub-type.
- **content_tokens**: Number of tokens in the element's text content (name + description), counted using the same deterministic tokenizer used by Token Points.
- **content_multiplier**: A global multiplier (default 0.1) that scales the content contribution relative to Bloom weights.

With the default multiplier of 0.1, a 100-token description contributes 10.0 to the score — comparable to a "create"-level Bloom weight of 8.0. Organizations can tune this value via calibration YAML.

## Token Counting Method

Content tokenization reuses the same infrastructure as Token Points (spec 038): tiktoken (`cl100k_base`) if installed, falling back to `max(1, len(text) // 4)` character-count heuristic. A warning is logged when the fallback is active.

## Content Sources per Element Type

Content is extracted as `name + " " + description` concatenation:

- **CSM Elements** (SpecificationActivity, Decision, Assumption, Constraint, Risk, OpenQuestion, AcceptanceCriterion, GlossaryTerm): Content = element's description text.
- **CSM References**: Content = `title + " " + url`.
- **CFM Elements** (FunctionalProcess, BusinessRule, Operation, DataGroup, Actor): Content = `name + " " + description`.
- **CFM Relationships**: Content = `name` only (no description field).

## Sub-Type Bloom Classification

The Bloom classifier supports sub-type differentiation via a three-tier lookup:

1. `base_type.sub_type_value` (e.g., `business_rule.derivation` → evaluate/5.0) — if the element has sub-type metadata
2. `base_type` (e.g., `business_rule` → apply/3.0) — the existing flat mapping
3. `default_bloom_level` — now "understand" (2.0) instead of the previous "analyze" (4.0)

Default sub-type mappings include BusinessRules (constraint → apply, condition → analyze, policy → evaluate, derivation → evaluate) and Operations (standard → apply, conditional → analyze, iterative → analyze, transactional → create). Elements without sub-type metadata continue to use their base type mapping.

## Updated Calibration Defaults

- `content_multiplier`: 0.1 (new field enabling content-based estimation).
- `default_bloom_level`: Changed from "analyze" to "understand" for more conservative scoring of unknown element types.
- `bloom_mappings`: Extended with sub-type keys for BusinessRules and Operations.
- **Backward Compatibility**: Old calibration YAML files without `content_multiplier`, sub-type mappings, or the updated default level load correctly via Pydantic field defaults. Setting `content_multiplier: 0.0` reverts to pure Bloom taxonomy scoring.

## Usage Recommendations

Cognitive Points v2 values are comparable across specifications because the score is grounded in content volume. A specification with 2× the content volume produces proportionally higher raw scores. This enables:

- **Cross-specification cognitive comparability**: Compare the cognitive effort of different specifications on the same scale, regardless of SDD framework.
- **Kanban work item sizing**: Group specifications into cognitive-effort buckets based on raw scores as a conceptual heuristic (e.g., Small: < 50 CP, Medium: 50–200 CP, Large: > 200 CP). These thresholds are organizational conventions, not a software feature — teams calibrate them to their own context.
- **Portfolio planning**: Aggregate Cognitive Points across a backlog to identify which work items demand the most human cognitive effort for review and validation.

The `cognitive_content_tokens` and `cognitive_content_multiplier` fields in the measurement payload provide auditability: consumers can verify the multiplier used and the content tokens counted per element type.

---

# Bloom-Based Cognitive Model

Cognitive complexity is modeled using a configurable interpretation of **Bloom's Taxonomy**.

The default taxonomy includes:

- Remember
- Understand
- Apply
- Analyze
- Evaluate
- Create

Each canonical element is deterministically mapped to one cognitive level.

Organizations may redefine these mappings through configuration.

Bloom provides a consistent conceptual framework for representing increasing levels of human cognitive demand without prescribing specific numeric values.

---

# Modified Fibonacci Normalization

Raw cognitive scores are normalized into a configurable **Modified Fibonacci Scale**.

The purpose of normalization is not mathematical precision but planning consistency.

Organizations are expected to recognize Cognitive Points similarly to how agile teams interpret Story Points—while preserving deterministic calculation.

Unlike Story Points, however, Cognitive Points are **computed**, not estimated by the team.

The normalization profile is fully configurable.

---

# Calibration

The methodology intentionally externalizes all calibration parameters.

Configurable elements include:

- Bloom mappings
- cognitive weights
- penalties
- adjustment factors
- normalization thresholds
- modified Fibonacci values

Organizations may calibrate the model using historical engineering data.

No source code modification is required.

---

# Explainability

Every Cognitive Points result must be fully explainable.

Measurement reports identify:

- contributing canonical element
- originating canonical model
- Bloom classification
- applied cognitive weight
- partial contribution
- normalization result
- cumulative score

Every contribution remains traceable to its originating specification evidence.

---

# Determinism

Given identical canonical models and identical calibration profiles:

```text
Cognitive Points(A)

=

Cognitive Points(B)
```

The measurement must always be reproducible.

---

# Framework Independence

Cognitive Points never depend on OpenSpec, SpecKit, or any specification framework.

Instead:

```text
Specification Framework

↓

Evidence Graph

↓

Canonical Models

↓

Cognitive Points
```

The resulting measurement depends solely on canonical semantics.

---

# Relationship with Story Points

Cognitive Points are **not** intended to replace Story Points.

Story Points are team-specific, experience-based estimates.

Cognitive Points are deterministic engineering measurements.

Organizations may choose to:

- use Cognitive Points directly for planning;
- use them to support Story Point estimation;
- compare estimated Story Points with measured Cognitive Points;
- replace Story Points in AI-first engineering environments.

The methodology intentionally leaves this organizational decision outside its scope.

---

# Integration with SpecMetrics

Cognitive Points are implemented as a standard Measurement Engine plugin.

Pipeline integration:

```text
Repository

↓

Evidence Graph

↓

Canonical Functional Model

↓

Canonical Specification Model

↓

Cognitive Points

↓

Export

↓

Telemetry
```

---

# Telemetry

Future releases may compare:

Estimated Cognitive Points

versus

Actual Human Review Effort

Possible calibration inputs include:

- review duration
- approval cycles
- clarification iterations
- defect escape rate
- review comments
- rework frequency

Telemetry is used only for calibration.

The deterministic Cognitive Points measurement remains the authoritative engineering metric.

---

# Future Work

Potential future enhancements include:

- automatic calibration from engineering telemetry
- machine learning-assisted cognitive calibration
- specification maturity indices
- review capacity forecasting
- cognitive bottleneck analysis
- engineering workload dashboards
- confidence intervals
- organization-specific cognitive profiles

---

# Alternatives Considered

## Story Points

Rejected.

Story Points are intentionally subjective and team-dependent.

SpecMetrics requires deterministic, reproducible measurements.

---

## Cyclomatic Complexity

Rejected.

Cyclomatic Complexity measures software implementation complexity rather than human cognitive effort during specification and validation.

---

## Cognitive Complexity (Code Metrics)

Rejected.

Existing cognitive complexity metrics operate on source code after implementation.

SpecMetrics estimates cognitive effort before implementation using software specifications.

---

## Time-Based Estimation

Rejected.

Elapsed review time depends on team composition, experience, organizational practices, and tooling.

Cognitive Points intentionally estimate intellectual workload rather than duration.

---

# Rationale

Cognitive Points introduce a new engineering metric aligned with AI-assisted software development.

As implementation becomes increasingly automated, human effort migrates toward higher-order cognitive activities: understanding, analyzing, evaluating, validating, and making decisions.

By combining the Canonical Specification Model, the Canonical Functional Model, and a configurable Bloom-inspired cognitive model, Cognitive Points provide a deterministic and explainable representation of this emerging engineering cost.

Together with Function Points, SNAP, and Token Points, Cognitive Points complete the measurement portfolio of SpecMetrics by addressing the fourth major engineering resource:

- **Function Points** measure _functional size_.
- **SNAP** measures _non-functional complexity_.
- **Token Points** measure _AI computational effort_.
- **Cognitive Points** measure _human cognitive effort_.

This combination enables organizations to plan AI-assisted software delivery using objective, reproducible, and framework-independent engineering metrics, establishing the foundation for the emerging discipline of **AI Engineering Economics**.
