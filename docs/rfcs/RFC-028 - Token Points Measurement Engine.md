# RFC-028 — Token Points Measurement Engine

**Status:** Draft

**Authors:** SpecMetrics Project

**Created:** 2026-07-17

**Target Release:** 0.3 – AI Engineering Metrics

---

# Abstract

This RFC introduces **Token Points (TP)**, a deterministic measurement methodology for estimating the expected computational cost of AI-assisted software engineering.

Unlike traditional software sizing techniques—which estimate functional size (Function Points), implementation effort (Story Points), or non-functional complexity (SNAP)—Token Points estimate the amount of Large Language Model (LLM) computation expected to transform a software specification into an implemented solution.

The measurement is independent of any specific LLM vendor, tokenizer, pricing model, or prompting strategy. Instead, it provides a stable engineering metric that organizations can calibrate to their own AI development environments.

---

# Motivation

Software engineering is entering a new economic model.

Historically, engineering planning focused on estimating:

- developer effort
- elapsed time
- functional size
- project cost

In AI-assisted software development, another scarce resource emerges:

**LLM computation.**

Organizations now manage:

- monthly token budgets
- API usage quotas
- model-specific pricing
- inference infrastructure
- AI engineering capacity

Today, there is no standardized methodology for estimating AI computational effort before implementation begins.

Token Points address this gap.

---

# Problem Statement

Current AI-assisted development lacks a deterministic way to answer questions such as:

- How much AI budget will this backlog require?
- Which feature consumes the largest amount of LLM computation?
- Is the available token budget sufficient for the next Program Increment?
- Which specifications should be prioritized given AI capacity constraints?

Current metrics provide no answer.

Function Points measure delivered functionality.

Story Points estimate implementation effort.

SNAP measures non-functional complexity.

None estimates AI computational consumption.

---

# Goals

Token Points aim to provide:

- deterministic estimation
- framework independence
- explainable calculations
- configurable organizational calibration
- planning support for AI-assisted development

The metric is intended for:

- Sprint Planning
- Kanban replenishment
- PI/IP Planning
- Portfolio planning
- AI budget forecasting
- Cost estimation
- Engineering governance

---

# Non-Goals

Token Points do **not** attempt to:

- predict actual token usage exactly
- estimate implementation duration
- estimate developer productivity
- optimize prompts
- benchmark LLMs
- replace billing systems

Actual token consumption remains dependent on:

- LLM provider
- tokenizer
- prompting strategy
- implementation workflow
- model architecture

---

# Conceptual Model

Token Points estimate **expected computational effort**, not actual token consumption.

The measurement is intentionally deterministic.

```
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
     Token Points Engine
```

The engine consumes two canonical models.

## Canonical Functional Model

Represents the software being built.

Contributes to:

- code generation cost

## Canonical Specification Model

Represents the engineering work required to produce the specification.

Contributes to:

- specification cost

---

# Measurement Model

The fundamental equation is:

```
Token Points

=

Specification Cost

+

Code Generation Cost
```

Both components are calculated independently.

---

## Specification Cost

Represents the computational effort required during specification engineering.

Examples include:

- exploration
- clarification
- refinement
- review
- validation

Additional specification artifacts contribute as well:

- decisions
- assumptions
- risks
- constraints
- acceptance criteria
- glossary terms
- open questions

---

## Code Generation Cost

Represents the computational effort expected during implementation.

Examples include:

- functional processes
- business rules
- operations
- relationships
- data groups
- actors

---

# Calibration

The methodology intentionally avoids embedding hardcoded values.

Instead, Token Points use externally configurable calibration profiles.

Calibration may include:

- element weights
- multipliers
- adjustment factors
- organization-specific rules

Organizations are expected to refine calibration using historical telemetry.

---

# Explainability

Every Token Points result must be explainable.

A measurement report should identify:

- contributing canonical element
- canonical model (CFM or CSM)
- applied weight
- partial contribution
- cumulative score

No score may be produced without traceability.

---

# Determinism

Given identical canonical models and identical calibration profiles:

```
Token Points(A)

=

Token Points(B)
```

The measurement must be reproducible.

---

# Framework Independence

Token Points never consume OpenSpec, SpecKit, or any framework directly.

Instead:

```
Specification Framework

↓

Evidence Graph

↓

Canonical Models

↓

Token Points
```

This guarantees identical measurements regardless of the originating specification framework.

---

# Configuration

Organizations may provide their own calibration profile.

Typical configurable parameters include:

- activity weights
- functional element weights
- adjustment factors
- organization policies

No source code modification is required.

---

# Telemetry

Future versions may compare:

Estimated Token Points

versus

Actual LLM Token Consumption

This enables continuous calibration while preserving deterministic measurements.

The deterministic estimate remains the authoritative engineering metric.

Telemetry is used exclusively for improving calibration.

---

# Integration with SpecMetrics

Token Points are implemented as a standard Measurement Engine plugin.

Pipeline integration:

```
Repository

↓

Evidence Graph

↓

Canonical Functional Model

↓

Canonical Specification Model

↓

Token Points

↓

Export

↓

Telemetry
```

The measurement follows the same lifecycle as Function Points, SNAP, and future measurement engines.

---

# Future Work

Future releases may introduce:

- automatic calibration from historical projects
- machine learning-assisted weight optimization
- organization-specific calibration profiles
- project-level Token Budget forecasting
- cost estimation based on cloud pricing
- AI ROI dashboards
- integration with OpenTelemetry metrics
- estimation confidence intervals

---

# Alternatives Considered

## Direct Token Prediction

Rejected.

Actual token usage depends on implementation details that are intentionally outside the scope of SpecMetrics.

---

## Model-Specific Estimation

Rejected.

Embedding GPT, Claude, Gemini or other tokenizer characteristics would compromise framework independence and long-term stability.

---

## Prompt-Length Estimation

Rejected.

Prompt size alone is a poor predictor of computational effort and ignores semantic complexity.

---

# Rationale

Token Points establish a new category of engineering measurement.

Rather than measuring software size or implementation effort, they measure the expected computational resources required to build software with AI assistance.

This enables organizations to manage AI capacity using the same engineering discipline traditionally applied to staffing, infrastructure, and financial planning.

By remaining deterministic, explainable, configurable, and framework-independent, Token Points become a foundational metric for the emerging discipline of **AI Engineering Economics**.
