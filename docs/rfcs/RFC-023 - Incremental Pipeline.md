# RFC-023 — Incremental Pipeline

**Release:** 0.2 – Knowledge Layer

**Status:** Draft

**Authors:** SpecMetrics Project

**Target Version:** 0.2

---

# 1. Summary

This RFC introduces the **Incremental Pipeline**, a deterministic execution model that reprocesses only the semantic knowledge affected by changes between executions.

Instead of rebuilding the entire Semantic Measurement Pipeline for every execution, the Incremental Pipeline identifies which portions of the Canonical Functional Model have changed and limits downstream processing to the impacted semantic concepts.

The Incremental Pipeline operates on persisted semantic artifacts rather than source documents, making semantic evolution the unit of execution.

---

# 2. Motivation

Release 0.1 executes the complete pipeline every time.

```text
Repository

↓

Extraction

↓

Evidence Graph

↓

CFM

↓

Validation

↓

Measurement
```

Even a minor documentation change causes the entire semantic model to be rebuilt.

As repositories grow, this approach becomes increasingly expensive.

Most software changes affect only a small subset of the business model.

The Incremental Pipeline minimizes unnecessary work by processing only semantic changes.

---

# 3. Goals

The Incremental Pipeline shall:

- detect semantic changes between executions;
- rebuild only affected semantic concepts;
- reuse unchanged knowledge;
- preserve deterministic behavior;
- reduce execution time;
- minimize LLM invocations;
- maintain full traceability.

---

# 4. Non Goals

This RFC does not introduce:

- parallel execution;
- distributed processing;
- speculative execution;
- background indexing;
- Git integration;
- document caching.

The pipeline remains synchronous and deterministic.

---

# 5. Architectural Position

```text
Previous CFM

        │

Current Specification

        │

Semantic Extraction

        │

Candidate CFM

        │

Semantic Diff Engine

        │

Changed Concepts

        │

Incremental Pipeline

        │

Updated Knowledge

        │

Measurement
```

The Semantic Diff Engine provides the change set consumed by the Incremental Pipeline.

---

# 6. Design Principles

## Knowledge-Centric Execution

Incrementality is based on semantic knowledge.

Never on files.

---

## Deterministic

The same repository state always produces the same pipeline result.

---

## Immutable Knowledge

Persisted CFMs remain immutable.

Incremental execution produces a new version.

---

## Dependency Awareness

Only concepts depending on changed knowledge are reprocessed.

---

## Traceability

Every reused artifact remains traceable to its originating evidence.

---

# 7. Processing Model

The pipeline evaluates semantic concepts individually.

```text
Actor

Business Entity

Business Rule

Relationship

Functional Process

Operation
```

Each concept becomes an execution unit.

---

# 8. Change Detection

The Incremental Pipeline consumes the Semantic Diff.

Example

```text
Previous CFM

↓

Semantic Diff

↓

Changed Concepts

↓

Execution Plan
```

Only modified concepts become candidates for processing.

---

# 9. Dependency Graph

Each semantic concept maintains dependency relationships.

Example

```text
Customer

↓

Register Customer

↓

Business Rule

↓

Create Account
```

A modification propagates through dependent concepts.

---

# 10. Execution Planning

The pipeline generates an execution plan.

Example

```text
Changed Entity

↓

Affected Processes

↓

Affected Rules

↓

Affected Measurement

↓

Affected Export
```

The execution plan is deterministic.

---

# 11. Reuse Strategy

Unchanged concepts are reused directly from persisted knowledge.

```text
Persisted CFM

↓

Load

↓

Reuse

↓

Updated CFM
```

No semantic extraction occurs for reused concepts.

---

# 12. Invalidation

Concepts become invalid when:

- directly modified;
- dependency modified;
- evidence changed;
- validation failed.

Invalid concepts are rebuilt.

---

# 13. Incremental Validation

Validation executes only for affected concepts.

Example

```text
Changed Rule

↓

Validate Rule

↓

Validate Dependencies
```

Global validation remains available through a full pipeline execution.

---

# 14. Incremental Measurement

Measurement plugins receive only affected concepts.

```text
Changed Functional Process

↓

Measurement Plugin

↓

Updated Measurement
```

Measurement methodologies decide how incremental updates are applied.

---

# 15. Pipeline States

Execution states

```text
NEW

REUSED

UPDATED

INVALIDATED

FAILED
```

Each semantic concept receives one state.

---

# 16. Cache Model

The pipeline maintains a semantic cache.

```text
Knowledge Repository

↓

Persisted CFM

↓

Semantic Cache

↓

Incremental Execution
```

The cache is an implementation detail.

Semantic correctness never depends on cache availability.

---

# 17. Execution Report

Example

```text
Incremental Execution Report

Concepts

Reused

148

Updated

6

Added

2

Removed

1

Execution Reduction

96%

LLM Calls Saved

94%

Measurement Reused

97%
```

---

# 18. CLI

New options

```bash
specmetrics measure --incremental

specmetrics build --incremental

specmetrics validate --incremental
```

Force complete rebuild

```bash
specmetrics measure --full
```

---

# 19. MCP

New tools

```text
Incremental Build

Incremental Measurement

Execution Plan

Changed Concepts
```

---

# 20. Public Events

```text
IncrementalExecutionStarted

ExecutionPlanGenerated

ConceptReused

ConceptUpdated

ConceptInvalidated

IncrementalExecutionCompleted
```

These events complement the existing pipeline lifecycle.

---

# 21. Pipeline Context

The Pipeline Context is extended with incremental execution metadata.

```yaml
incremental:
  enabled: true

  previous_cfm:

  execution_plan:

  reused_concepts:

  updated_concepts:

  invalidated_concepts:

  rebuild_reason:
```

This metadata is immutable throughout execution.

---

# 22. Plugin Contract

Pipeline stages may optionally support incremental execution.

```python
class IncrementalStage:

    execute(
        changes,
        previous_state,
        context
    ) -> StageResult
```

Stages that do not implement this contract execute normally.

The Kernel transparently falls back to full execution.

---

# 23. Compatibility

Incremental execution is optional.

Every command supports two execution modes.

```text
Full Pipeline

Incremental Pipeline
```

Both must produce identical semantic results.

The only difference is execution efficiency.

---

# 24. Relationship with Other RFCs

The Incremental Pipeline depends on previously established Knowledge Layer capabilities.

| RFC                                  | Contribution                                   |
| ------------------------------------ | ---------------------------------------------- |
| RFC-020 — Semantic Validation Engine | Validates updated concepts before reuse        |
| RFC-021 — Semantic Diff Engine       | Identifies semantic changes between executions |
| RFC-022 — CFM Persistence            | Provides immutable semantic snapshots          |
| RFC-024 — Semantic Query Engine      | Exposes execution plans and changed concepts   |
| RFC-026 — Measurement Repository     | Stores incremental measurement history         |
| RFC-027 — Pipeline Observability     | Measures incremental execution performance     |

The Incremental Pipeline does not introduce new semantic concepts. Instead, it orchestrates the reuse and selective recomputation of persisted knowledge.

---

# 25. Future Evolution

The Incremental Pipeline establishes semantic incrementality as a core architectural capability of SpecMetrics. Future releases may expand this model with:

- parallel execution of independent semantic subgraphs;
- distributed pipeline execution;
- predictive dependency analysis;
- semantic prefetching;
- background knowledge indexing;
- fine-grained LLM request optimization;
- incremental semantic extraction;
- incremental Evidence Graph maintenance;
- cross-repository dependency analysis;
- semantic build acceleration metrics.

By making semantic concepts—not documents or source files—the unit of incremental execution, the SpecMetrics pipeline aligns with modern compiler architectures while preserving its knowledge-centric design. This approach dramatically reduces processing costs, minimizes unnecessary LLM usage, and enables scalable semantic engineering without compromising determinism, explainability, or traceability.
