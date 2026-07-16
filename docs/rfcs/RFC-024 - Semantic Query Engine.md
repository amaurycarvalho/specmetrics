# RFC-024 — Semantic Query Engine

**Release:** 0.2 – Knowledge Layer

**Status:** Draft

**Authors:** SpecMetrics Project

**Target Version:** 0.3

---

# 1. Summary

This RFC introduces the **Semantic Query Engine**, a deterministic query subsystem that enables structured access to persisted semantic knowledge stored in the Knowledge Repository.

Rather than searching Markdown documents or specification files, the Semantic Query Engine operates exclusively on persisted **Canonical Functional Models (CFMs)** and their associated semantic artifacts.

The engine provides a unified query interface for humans, AI agents and downstream platform components, exposing engineering knowledge independently from its original specification framework.

---

# 2. Motivation

Release 0.2 establishes persistent Canonical Functional Models.

Once knowledge becomes persistent, users and tools require mechanisms to explore, inspect and retrieve semantic concepts without rebuilding the entire Semantic Measurement Pipeline.

Traditional document search answers questions such as:

- Which document contains "Customer"?

The Knowledge Layer should answer questions such as:

- Which Functional Processes manipulate Customer?
- Which Business Rules affect Invoice?
- Which Actors perform Approval?
- Which evidence supports this relationship?

The Semantic Query Engine fulfills this role.

---

# 3. Goals

The Semantic Query Engine shall:

- query persisted semantic knowledge;
- operate exclusively on Canonical Functional Models;
- provide deterministic query results;
- preserve complete evidence traceability;
- expose reusable APIs for AI agents;
- remain independent from specification frameworks;
- support future semantic indexes.

---

# 4. Non Goals

This RFC does not introduce:

- natural language search;
- vector databases;
- embeddings;
- full-text document search;
- LLM reasoning;
- graph databases.

Queries operate on canonical semantic structures.

---

# 5. Architectural Position

```text
Knowledge Repository

        │

Persisted CFM

        │

Semantic Query Engine

        │

Query Result

        │

CLI

MCP

Measurement

Validation

AI Agents
```

The Query Engine becomes the primary access point to semantic knowledge.

---

# 6. Design Principles

## Knowledge First

Queries operate on semantic concepts.

Never on Markdown.

---

## Deterministic

The same query executed against the same CFM always produces identical results.

---

## Read Only

Queries never modify persisted knowledge.

---

## Framework Independence

The engine knows nothing about:

- OpenSpec
- SpecKit
- Markdown
- Prompt templates

---

## Explainability

Every returned concept references its supporting evidence.

---

# 7. Query Model

Every query consists of

```yaml
target:

filters:

projection:

ordering:

limit:
```

The query model is intentionally independent of storage technology.

---

# 8. Supported Targets

Release 0.2 supports querying:

- Actors
- Functional Processes
- Business Entities
- Operations
- Business Rules
- Relationships
- Evidence
- Diagnostics
- Measurements
- Metadata

Future concepts automatically become queryable.

---

# 9. Query Types

The engine supports four query categories.

---

## Lookup

Retrieve a specific concept.

Example

```text
Find Actor "Customer"
```

---

## List

Retrieve collections.

Example

```text
List Functional Processes
```

---

## Filter

Retrieve concepts matching conditions.

Example

```text
Business Rules

where

severity = HIGH
```

---

## Traversal

Navigate semantic relationships.

Example

```text
Customer

↓

Processes

↓

Business Rules

↓

Evidence
```

Traversal is deterministic.

---

# 10. Relationship Navigation

Queries may traverse semantic relationships.

Example

```text
Actor

↓

Functional Process

↓

Operation

↓

Business Entity
```

Every traversal preserves provenance.

---

# 11. Evidence Queries

Every concept exposes supporting evidence.

Example

```text
Business Rule

↓

Evidence

↓

Specification Fragment
```

Evidence remains immutable.

---

# 12. Metadata Queries

Metadata may also be queried.

Examples

- creation date;
- repository;
- Git commit;
- semantic provider;
- validation status;
- schema version.

Metadata queries never affect semantic results.

---

# 13. Query Result

Every query returns

```yaml
query:

result:

count:

execution_time:

cfm_version:

evidence:
```

Result ordering is deterministic.

---

# 14. CLI

New command

```bash
specmetrics query
```

Examples

```bash
specmetrics query actors

specmetrics query entities

specmetrics query processes

specmetrics query rules

specmetrics query evidence

specmetrics query relationships
```

Filtering

```bash
specmetrics query rules --entity Customer

specmetrics query processes --actor Manager

specmetrics query entities --name Invoice
```

---

# 15. MCP

New tools

```text
Search Knowledge

List Concepts

Describe Concept

Traverse Relationships

Find Evidence

List Business Rules

List Functional Processes
```

The MCP interface exposes semantic knowledge independently from implementation details.

---

# 16. Public Events

Queries are observable.

```text
QueryStarted

QueryCompleted

QueryFailed
```

Read-only operations never modify pipeline state.

---

# 17. Query Language

Release 0.2 introduces a simple deterministic query language.

Examples

```text
actors
```

```text
entities
```

```text
processes
```

```text
rules
```

```text
actor:Customer
```

```text
entity:Invoice
```

```text
process:Register Customer
```

Future releases may introduce richer syntax while preserving backward compatibility.

---

# 18. Plugin Interface

Alternative query providers may be implemented.

```python
class QueryProvider:

    execute(
        query,
        cfm
    ) -> QueryResult
```

The platform Kernel remains unaware of query implementation details.

---

# 19. Integration with Other Components

The Semantic Query Engine serves as a shared read layer.

Consumers include:

- Validation Engine
- Semantic Diff Engine
- Measurement Repository
- AI Agents
- Export Plugins
- CLI
- MCP Server

No component accesses persisted knowledge directly.

---

# 20. Security

The Query Engine is read-only.

Queries:

- never modify CFMs;
- never alter evidence;
- never update metadata.

Authorization policies are outside the scope of this RFC.

---

# 21. Performance

The engine should optimize repeated queries through implementation-specific caching mechanisms.

Caching must:

- remain transparent to callers;
- preserve deterministic behavior;
- never return stale semantic data.

Performance optimizations must not change query semantics.

---

# 22. Relationship with Other RFCs

The Semantic Query Engine builds upon previously established Knowledge Layer capabilities.

| RFC                                  | Contribution                                               |
| ------------------------------------ | ---------------------------------------------------------- |
| RFC-020 — Semantic Validation Engine | Exposes validation diagnostics as queryable concepts       |
| RFC-021 — Semantic Diff Engine       | Allows querying semantic differences and impacted concepts |
| RFC-022 — CFM Persistence            | Provides the persisted knowledge repository                |
| RFC-023 — Incremental Pipeline       | Enables inspection of execution plans and reused concepts  |
| RFC-026 — Measurement Repository     | Makes historical measurements queryable                    |
| RFC-027 — Pipeline Observability     | Exposes execution telemetry through semantic queries       |

The Query Engine does not own semantic knowledge; it provides deterministic access to the Knowledge Repository.

---

# 23. Future Evolution

The Semantic Query Engine establishes the Knowledge Layer as an accessible semantic platform rather than a passive repository. Future releases may extend this subsystem with:

- natural language query translation;
- GraphQL interface;
- semantic graph query language;
- vector-based semantic search;
- ontology-aware reasoning;
- federated queries across repositories;
- AI-assisted query generation;
- semantic autocomplete;
- saved query catalogs;
- cross-project knowledge discovery.

By making persisted Canonical Functional Models directly queryable, the Semantic Query Engine completes the transformation of SpecMetrics from a deterministic measurement pipeline into a reusable semantic knowledge platform. It enables both humans and AI agents to interact with engineering knowledge through a stable, framework-independent interface, reinforcing the Knowledge Layer as the canonical source of functional understanding across the entire platform.
