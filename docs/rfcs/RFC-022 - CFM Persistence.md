# RFC-022 — CFM Persistence

**Release:** 0.2 – Knowledge Layer

**Status:** Draft

**Authors:** SpecMetrics Project

**Target Version:** 0.3

---

# 1. Summary

This RFC introduces persistent storage for the **Canonical Functional Model (CFM)**.

Instead of existing only during pipeline execution, every generated CFM becomes a versioned engineering artifact that can be stored, queried, compared and reused by downstream platform capabilities.

Persistent CFMs establish the foundation of the **Knowledge Layer**, allowing semantic knowledge to survive beyond a single measurement execution.

---

# 2. Motivation

Release 0.1 builds the Canonical Functional Model as an intermediate pipeline artifact.

Once measurement finishes, the model is discarded.

This prevents:

- semantic history;
- incremental processing;
- semantic comparison;
- knowledge reuse;
- historical measurements;
- offline analysis.

Persisting the Canonical Functional Model transforms semantic knowledge into a durable engineering asset.

---

# 3. Goals

The CFM Persistence subsystem shall:

- persist every Canonical Functional Model;
- preserve complete semantic information;
- preserve evidence references;
- support immutable versions;
- support deterministic reconstruction;
- provide reusable inputs for downstream services;
- remain independent from measurement methodologies.

---

# 4. Non Goals

This RFC does not introduce:

- relational databases;
- enterprise repositories;
- collaborative editing;
- document management;
- distributed synchronization;
- semantic search.

Persistence stores knowledge.

It does not manage specifications.

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

CFM Persistence

↓

Knowledge Repository

↓

Validation

Measurement

Semantic Diff

Query Engine

AI Agents
```

The persistent repository becomes the central source of semantic knowledge.

---

# 6. Design Principles

## Immutable Artifacts

Every persisted CFM is immutable.

Updates always generate new versions.

---

## Canonical Representation

Only Canonical Functional Models are persisted.

Never framework-specific documents.

---

## Framework Independence

The persistence layer knows nothing about:

- OpenSpec
- SpecKit
- Markdown
- LLM providers

---

## Deterministic Reconstruction

Loading a persisted CFM must reproduce exactly the same semantic model.

---

## Local First

Persistent storage resides entirely under user control.

No external infrastructure is required.

---

# 7. Repository Structure

Each repository contains its own knowledge store.

Example

```text
.specmetrics/

    knowledge/

        cfm/

            cfm-000001/

            cfm-000002/

            cfm-000003/
```

Each CFM is stored independently.

---

# 8. CFM Package

A persisted CFM is stored as a self-contained package.

Example

```text
cfm-000003/

    metadata.json

    cfm.json

    evidence.json

    graph.json

    diagnostics.json

    manifest.json
```

The package is immutable once created.

---

# 9. Manifest

Every package contains metadata describing its origin.

Example

```yaml
id: cfm-000003

version: 3

created_at:

repository:

commit:

adapter:

semantic_provider:

model:

validation_pack:

specmetrics_version:

schema_version:
```

The manifest enables reproducibility.

---

# 10. Stored Components

Every persisted package includes:

- Canonical Functional Model
- Evidence Graph
- Validation Diagnostics
- Metadata
- Provenance Information

Future releases may include:

- semantic embeddings;
- cached measurements;
- semantic indexes.

---

# 11. Identity

Each persisted CFM receives a globally unique identifier.

```text
CFM

↓

UUID

↓

Immutable Version
```

Identity never changes.

---

# 12. Versioning

Versions are append-only.

Example

```text
CFM

v1

↓

v2

↓

v3
```

Previous versions are never modified.

---

# 13. Metadata

Each persisted model stores execution metadata.

Examples

- creation timestamp;
- Git commit;
- repository hash;
- semantic provider;
- provider version;
- model name;
- adapter version;
- validation result.

Metadata does not affect semantic content.

---

# 14. Persistence Lifecycle

```text
CanonicalModelBuilt

↓

Validate

↓

Persist

↓

CFMPersisted

↓

Measurement
```

Persistence occurs immediately after successful validation.

---

# 15. CLI

New command

```bash
specmetrics build
```

Produces

```text
Validated CFM

↓

Persistent Package
```

Additional commands

```bash
specmetrics build

specmetrics list

specmetrics show

specmetrics delete

specmetrics export
```

---

# 16. MCP

New tools

```text
Build Knowledge Layer

List Models

Load Model

Describe Model

Delete Model
```

---

# 17. Loading

Persisted CFMs may be loaded without reprocessing specifications.

```text
CFM Package

↓

Load

↓

Canonical Functional Model

↓

Measurement

Validation

Query

Diff
```

This avoids unnecessary semantic extraction.

---

# 18. Pipeline Integration

Subsequent pipeline stages consume persisted models directly.

```text
Measure

↓

Load CFM

↓

Measurement Engine
```

instead of

```text
Read Markdown

↓

Semantic Extraction

↓

Evidence Graph

↓

CFM
```

when no rebuild is required.

---

# 19. Public Events

```text
PersistenceStarted

CFMPersisted

PersistenceFailed

CFMLoaded
```

These events become part of the canonical pipeline.

---

# 20. Plugin Interface

```python
class PersistenceProvider:

    save(
        cfm
    ) -> CFMReference

    load(
        reference
    ) -> CanonicalFunctionalModel

    list() -> Iterable[CFMReference]

    delete(reference)
```

Alternative storage providers may be implemented as plugins.

---

# 21. Repository API

The persistence layer exposes deterministic operations.

```text
Save

Load

List

Exists

Delete

Describe
```

These operations remain independent of storage technology.

---

# 22. Storage Providers

Release 0.2 defines a local filesystem implementation as the reference provider.

Future providers may include:

- SQLite;
- PostgreSQL;
- Object Storage;
- Git-backed repositories;
- Cloud storage services.

All providers expose the same contract.

---

# 23. Compatibility

Persisted models include explicit schema versions.

```yaml
schema_version: 1

cfm_version: 1

specmetrics_version: 0.2
```

Future releases shall support backward compatibility whenever feasible.

Migration strategies remain outside the scope of this RFC.

---

# 24. Relationship with Other RFCs

CFM Persistence is a foundational capability for the Knowledge Layer.

Subsequent RFCs depend on persisted semantic knowledge:

| RFC                              | Dependency                                        |
| -------------------------------- | ------------------------------------------------- |
| RFC-021 — Semantic Diff Engine   | Compare persisted CFMs                            |
| RFC-023 — Incremental Pipeline   | Detect previously processed knowledge             |
| RFC-024 — Semantic Query Engine  | Query persisted semantic models                   |
| RFC-026 — Measurement Repository | Associate measurements with specific CFM versions |
| RFC-027 — Pipeline Observability | Measure lifecycle events of persisted artifacts   |

This RFC intentionally introduces no measurement-specific concepts, ensuring that the Knowledge Repository remains a methodology-independent semantic layer.

---

# 25. Future Evolution

The CFM Persistence subsystem establishes the Knowledge Repository as the central semantic asset store of SpecMetrics. Future releases may extend this capability with:

- content-addressable storage;
- semantic deduplication;
- compressed CFM packages;
- cryptographic integrity verification;
- digital signatures;
- semantic lineage tracking;
- distributed repositories;
- remote synchronization;
- semantic indexing;
- enterprise-scale storage providers.

By making the Canonical Functional Model persistent, SpecMetrics shifts from a transient processing pipeline to a knowledge-centric architecture. From this release onward, the CFM becomes a durable engineering artifact that can be validated, queried, compared, measured and analyzed repeatedly without requiring semantic re-extraction, reinforcing the long-term vision of the **Knowledge Layer** as the semantic backbone of the platform.
