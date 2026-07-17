# RFC-031 — Deterministic Semantic Engine

**RFC**: 031

**Title**: Deterministic Semantic Engine

**Status**: Draft

**Author**: SpecMetrics Team

**Created**: 2026-07-17

**Related Specification**: F28 – Deterministic Semantic Engine

---

# Summary

This RFC defines the deterministic implementation of the Semantic Extraction Engine.

Instead of relying on LLMs, the engine extracts semantic elements using structural analysis, framework conventions and deterministic heuristics.

The implementation enables the entire SpecMetrics pipeline to operate completely offline.

---

# Motivation

Semantic extraction should not require an AI provider.

Many environments require:

- offline execution
- deterministic behavior
- reproducible results
- zero operational cost

The Deterministic Semantic Engine satisfies these requirements.

---

# Goals

- Zero external dependencies.
- Fully deterministic execution.
- Evidence-first extraction.
- Framework-aware parsing.
- Extensible rule library.

---

# Non-Goals

This RFC does not attempt to reproduce LLM reasoning.

Implicit semantic inference remains outside its scope.

---

# Processing Pipeline

```
Documents
      │
      ▼
Markdown Parser
      │
      ▼
AST
      │
      ▼
Visitors
      │
      ▼
Rule Engine
      │
      ▼
Pattern Library
      │
      ▼
ExtractionResult
```

---

# Parsing

Markdown is parsed into an Abstract Syntax Tree.

Regular expressions are not the primary parsing mechanism.

---

# Visitors

Visitors traverse the AST.

Examples:

- HeadingVisitor
- ListVisitor
- TableVisitor
- ParagraphVisitor
- CodeBlockVisitor
- QuoteVisitor

Each visitor contributes semantic observations.

---

# Rule Engine

Rules transform structural observations into semantic elements.

Examples:

```
Heading "Actors"

↓

Actor Section
```

```
Heading "Business Rules"

↓

Business Rule Section
```

```
Heading "Acceptance Criteria"

↓

Acceptance Criteria Section
```

---

# Pattern Library

Patterns identify common specification structures.

Examples:

```
Given

When

Then
```

↓

Acceptance Criteria

---

```
As a...

I want...

So that...
```

↓

User Story

---

```
Must

Shall

Should
```

↓

Requirement

---

```
If

Then
```

↓

Business Rule

---

# Framework Awareness

Framework-specific conventions are supported.

Examples:

- OpenSpec
- SpecKit

Each framework contributes deterministic extraction rules.

---

# Evidence Preservation

Every extracted element includes:

- document identifier
- section identifier
- original text
- extraction rule

Evidence is mandatory.

---

# Confidence

Confidence is deterministic.

Examples:

| Source               | Confidence |
| -------------------- | ---------- |
| Explicit heading     | 1.00       |
| Framework convention | 0.95       |
| Structural heuristic | 0.85       |
| Pattern inference    | 0.70       |

Confidence values are deterministic.

---

# Rule Packs

Rules are organized into independent packs.

Examples:

```
General Markdown

OpenSpec

SpecKit

BDD

User Stories

Business Rules

Requirements
```

Rule packs can evolve independently.

---

# Determinism

Given identical inputs:

- identical AST
- identical visitors
- identical rules

the engine MUST produce identical ExtractionResult objects.

---

# Extensibility

New rule packs may be added without modifying existing ones.

The engine remains compliant with the Open/Closed Principle.

---

# Performance

The engine should process documents in linear time relative to document size.

No network operations are performed.

---

# Future Work

Future deterministic capabilities may include:

- glossary linking
- terminology normalization
- document cross-references
- specification consistency checks
- ambiguity detection
- duplicate requirement detection
- structural quality analysis

These enhancements extend the rule library without changing the Semantic Extraction Engine abstraction defined in RFC-030.
