# RFC-025 — CFM Export Plugins

**Release:** 0.2 – Knowledge Layer

**Status:** Draft

**Authors:** SpecMetrics Project

**Target Version:** 0.2

---

# 1. Summary

This RFC introduces the **CFM Export Plugin Architecture**, enabling the export of persisted semantic knowledge into multiple external representations.

Unlike the Measurement Export Layer introduced in Release 0.1, which exports measurement results, this subsystem exports **Canonical Functional Models (CFMs)** and their associated semantic artifacts.

The exported representations are intended for documentation, visualization, interoperability, engineering analysis and AI-assisted workflows.

Every export format is implemented as an independent plugin.

---

# 2. Motivation

The Knowledge Layer establishes the Canonical Functional Model as the central semantic asset of SpecMetrics.

Persisted knowledge should be reusable outside the platform.

Organizations may wish to:

- visualize semantic models;
- publish engineering documentation;
- integrate with graph databases;
- feed AI agents;
- exchange semantic knowledge with external systems.

A plugin-based export architecture enables these integrations without modifying the platform core.

---

# 3. Goals

The CFM Export subsystem shall:

- export persisted Canonical Functional Models;
- preserve semantic integrity;
- preserve evidence traceability;
- support multiple export formats;
- remain deterministic;
- allow third-party exporters;
- remain independent from storage technologies.

---

# 4. Non Goals

This RFC does not introduce:

- measurement export;
- report generation;
- PDF publishing;
- semantic editing;
- visualization engines;
- external synchronization.

Export plugins generate representations.

They never modify knowledge.

---

# 5. Architectural Position

```text
Knowledge Repository

        │

Persisted CFM

        │

CFM Export Layer

        │

Export Plugin

        │

Generated Artifact
```

Exporters consume semantic knowledge only.

---

# 6. Design Principles

## Canonical Source

All exporters consume the Canonical Functional Model.

Never specifications.

Never Markdown.

---

## Read Only

Export never modifies persisted knowledge.

---

## Deterministic

The same CFM always produces identical exported artifacts.

---

## Plugin-Oriented

Every export format is implemented independently.

---

## Extensible

New formats may be added without changing the Kernel.

---

# 7. Export Targets

The export layer supports different semantic artifacts.

- Canonical Functional Model
- Evidence Graph
- Semantic Diff
- Validation Report
- Metadata
- Knowledge Manifest

Each exporter declares the artifacts it supports.

---

# 8. Built-in Export Formats

Release 0.2 defines the following reference exporters.

---

## JSON

Canonical machine-readable representation.

Use cases

- APIs
- AI agents
- integrations
- persistence

---

## YAML

Human-readable structured representation.

Use cases

- review
- configuration
- documentation

---

## Markdown

Engineering documentation.

Use cases

- Git repositories
- documentation portals
- architecture reviews

---

## GraphML

Graph representation.

Use cases

- Neo4j
- Gephi
- Cytoscape

---

## Mermaid

Diagram generation.

Examples

```text
graph TD

Customer

-->

Order

-->

Invoice
```

---

## PlantUML

Architecture diagrams.

Example

```text
Actor

-->

Functional Process

-->

Business Entity
```

---

# 9. Future Export Formats

Future plugins may support

- D2
- Structurizr DSL
- GraphSON
- RDF
- OWL
- DOT
- CSV
- XML
- HTML
- PDF
- Obsidian Vault
- MkDocs
- AsciiDoc

No Kernel modification is required.

---

# 10. Export Model

Each export operation receives

```yaml
cfm:

artifact:

format:

options:

destination:
```

The model is format-independent.

---

# 11. Export Package

Generated artifacts may contain

```text
knowledge/

    cfm.*

    evidence.*

    metadata.*

    validation.*

    manifest.*
```

Plugins determine which files are generated.

---

# 12. Manifest

Every exported package includes metadata.

Example

```yaml
cfm_version:

schema_version:

repository:

generated_at:

exporter:

specmetrics_version:
```

This metadata supports reproducibility.

---

# 13. CLI

New command

```bash
specmetrics export knowledge
```

Examples

```bash
specmetrics export knowledge --format json

specmetrics export knowledge --format yaml

specmetrics export knowledge --format markdown

specmetrics export knowledge --format graphml

specmetrics export knowledge --format mermaid

specmetrics export knowledge --format plantuml
```

---

# 14. MCP

New tools

```text
Export Knowledge

Export Graph

Export Documentation

Export Diagram
```

AI agents receive exported semantic artifacts without accessing persistence directly.

---

# 15. Plugin Discovery

Exporters are discovered through the Plugin Registry.

Example

```text
plugins/

    exporters/

        json/

        yaml/

        graphml/

        mermaid/

        plantuml/
```

Discovery follows the existing Plugin Architecture.

---

# 16. Plugin Interface

```python
class KnowledgeExporter:

    export(
        artifact,
        destination,
        options
    ) -> ExportResult
```

Every exporter implements the same contract.

---

# 17. Export Result

Each export returns

```yaml
artifact:

format:

generated_files:

duration:

warnings:

metadata:
```

Exporters never return semantic modifications.

---

# 18. Public Events

The export lifecycle emits deterministic events.

```text
KnowledgeExportStarted

KnowledgeExportCompleted

KnowledgeExportFailed
```

These events are observable through the Pipeline.

---

# 19. Relationship with Other RFCs

The export layer consumes artifacts produced by the Knowledge Layer.

| RFC                                  | Exportable Artifact                   |
| ------------------------------------ | ------------------------------------- |
| RFC-020 — Semantic Validation Engine | Validation Reports                    |
| RFC-021 — Semantic Diff Engine       | Semantic Diff                         |
| RFC-022 — CFM Persistence            | Persisted Canonical Functional Models |
| RFC-023 — Incremental Pipeline       | Execution Plans                       |
| RFC-024 — Semantic Query Engine      | Query Results                         |
| RFC-026 — Measurement Repository     | Measurement History                   |
| RFC-027 — Pipeline Observability     | Pipeline Metrics                      |

The export subsystem is intentionally agnostic regarding the semantic origin of the exported artifact.

---

# 20. Compatibility

Knowledge Export Plugins coexist with the existing Measurement Export Layer introduced in Release 0.1.

Their responsibilities remain clearly separated.

| Export Layer | Artifact            |
| ------------ | ------------------- |
| Release 0.1  | Measurement Results |
| Release 0.2  | Knowledge Artifacts |

Both layers share the same plugin philosophy while serving different architectural concerns.

---

# 21. Future Evolution

The CFM Export Plugin Architecture establishes interoperability as a first-class capability of the Knowledge Layer. Future releases may extend this subsystem with:

- streaming exporters;
- graph database connectors;
- documentation site generators;
- architecture modeling exports;
- enterprise repository integrations;
- semantic ontology exports;
- AI-ready knowledge packages;
- digital signatures for exported artifacts;
- export templates;
- multi-artifact export bundles.

By separating **knowledge export** from **measurement export**, SpecMetrics reinforces the architectural distinction between engineering knowledge and the analyses derived from it. The Canonical Functional Model becomes a portable semantic asset that can be consumed by documentation systems, visualization tools, graph platforms and AI ecosystems without coupling those integrations to the platform core, fulfilling the long-term vision of the **Knowledge Layer** as the canonical source of functional engineering knowledge.
