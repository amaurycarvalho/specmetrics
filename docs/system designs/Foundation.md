# System Design — Release 0.1 (Foundation)

```
1. Purpose
2. Scope
3. Architectural Drivers
4. High-Level Architecture
5. Semantic Measurement Pipeline
6. Core Components
7. Plugin Architecture
8. Canonical Functional Model
9. Data Flow
10. Project Structure
11. Technology Stack
12. Deployment Model
13. Installation
14. User Workflows
15. Configuration
16. Quality Attributes
17. Security
18. Future Evolution
Appendix A — Execution Sequences
```

---

# 1. Purpose

This document describes the software architecture of **SpecMetrics Release 0.1 (Foundation)**.

It complements the Product Requirements Document (PRD) by defining the technical architecture required to implement the first production-ready version of the platform.

Release 0.1 validates the core architectural hypothesis:

> Specification Driven Development artifacts can be transformed into deterministic, traceable and explainable functional measurements through a semantic processing pipeline.

---

# 2. Scope

This document covers:

- system architecture;
- semantic processing pipeline;
- plugin architecture;
- deployment model;
- technology choices;
- installation model;
- project organization.

Business requirements are intentionally excluded and are defined in the Product Requirements Document.

---

# 3. Architectural Drivers

The architecture is designed around the following drivers.

## Functional Drivers

- Automatic functional measurement
- SDD framework independence
- Deterministic measurement
- Explainability
- Traceability

## Quality Drivers

- Extensibility
- Maintainability
- Plugin-first
- AI-native
- Open Source
- Local-first

---

# 4. High-Level Architecture

```
                CLI
                 │
                 │
          MCP Server
                 │
                 ▼
        Application Layer
                 │
                 ▼
        Semantic Pipeline
                 │
                 ▼
     Canonical Functional Model
                 │
                 ▼
      Measurement Engine
                 │
                 ▼
 Exporters / Publishers
```

Only the Application Layer communicates with the outside world.

Everything below it is framework-independent.

---

# 5. Semantic Measurement Pipeline

The Semantic Measurement Pipeline is the execution model of SpecMetrics.

Rather than directly invoking subsequent processing stages, the Pipeline Engine coordinates execution through an internal event-driven architecture.

Each stage publishes immutable domain events describing the completion of its work. Interested components subscribe to these events and execute the next processing step.

This approach preserves deterministic execution while minimizing coupling between components.

```
Specification Repository
        │
        ▼
Pipeline Engine
        │
        ▼
RepositoryLoaded
        │
        ▼
Specification Adapter
        │
        ▼
DocumentsDiscovered
        │
        ▼
Semantic Extraction
        │
        ▼
SemanticExtractionCompleted
        │
        ▼
Evidence Graph
        │
        ▼
EvidenceGraphBuilt
        │
        ▼
Canonical Functional Model
        │
        ▼
CanonicalModelBuilt
        │
        ▼
Rule Pack Engine
        │
        ▼
RulePackApplied
        │
        ▼
Measurement Engine
        │
        ▼
MeasurementCompleted
        │
        ├────────────► Export Layer
        │                   │
        │                   ▼
        │             ExportCompleted
        │
        └────────────► Publisher Layer
                            │
                            ▼
                    TelemetryPublished
```

## Stage 1 — Specification Repository

Input:

- OpenSpec repository
- SpecKit repository

Outputs:

Repository abstraction.

---

## Stage 2 — Specification Adapter

Responsibilities

- Discover documents
- Read Markdown
- Build semantic reading order
- Preserve metadata

Output

SpecificationDocument collection.

---

## Stage 3 — Semantic Extraction

Responsibilities

- Invoke LLM
- Extract semantic concepts
- Preserve evidence
- Generate confidence

Output

Evidence Graph.

---

## Stage 4 — Evidence Graph

Responsibilities

- Store semantic facts
- Store evidence
- Preserve provenance
- Resolve references

Output

Knowledge graph.

---

## Stage 5 — Canonical Functional Model

Responsibilities

Normalize all semantic concepts.

Contains:

- Actors
- Functional Processes
- Business Rules
- Data Groups
- Relationships
- Operations

No framework-specific concepts exist beyond this point.

---

## Stage 6 — Rule Pack Engine

Responsibilities

Apply organizational rules.

Sources:

- YAML
- Markdown

Future:

- PDF
- RAG

---

## Stage 7 — Measurement Engine

Responsibilities

Execute deterministic measurements.

Supported plugins:

- FPA
- SFP
- SNAP

---

## Stage 8 — Export Layer

Supported:

- JSON
- CSV
- XML

---

## Stage 9 — Publisher Layer

Supported:

- OpenTelemetry

Future releases will add additional publishers.

---

# 6. Core Components

## Pipeline Engine

The Pipeline Engine is responsible for orchestrating the complete Semantic Measurement Pipeline.

Instead of invoking pipeline stages directly, it coordinates execution through an internal Event Bus.

Responsibilities include:

- starting pipeline execution;
- publishing pipeline events;
- resolving event handlers;
- enforcing execution order;
- collecting execution state;
- detecting failures;
- ensuring deterministic execution.

The Pipeline Engine owns the execution lifecycle of every measurement request.

---

## Event Bus

The Event Bus is an internal Kernel component responsible for dispatching pipeline events.

Characteristics:

- synchronous;
- in-process;
- deterministic;
- immutable events;
- ordered delivery;
- no external dependencies.

The Event Bus is **not** intended as an enterprise messaging infrastructure.

Its sole purpose is to decouple pipeline stages while preserving deterministic behavior.

---

# Internal Pipeline Events

Release 0.1 defines the following canonical events.

| Event                       | Published By            | Consumed By                       |
| --------------------------- | ----------------------- | --------------------------------- |
| RepositoryLoaded            | Pipeline Engine         | Specification Adapter             |
| DocumentsDiscovered         | Specification Adapter   | Semantic Extraction Provider      |
| SemanticExtractionCompleted | Semantic Provider       | Evidence Graph Builder            |
| EvidenceGraphBuilt          | Evidence Graph Builder  | Canonical Model Builder           |
| CanonicalModelBuilt         | Canonical Model Builder | Rule Pack Engine                  |
| RulePackApplied             | Rule Pack Engine        | Measurement Engine                |
| MeasurementCompleted        | Measurement Engine      | Export Plugins, Publisher Plugins |
| ExportCompleted             | Export Plugins          | Pipeline Engine                   |
| TelemetryPublished          | Publisher Plugins       | Pipeline Engine                   |
| PipelineCompleted           | Pipeline Engine         | CLI / MCP                         |

---

# Pipeline Execution State

Each execution creates a Pipeline Context.

```
PipelineContext

- execution_id
- repository
- adapter
- semantic_provider
- measurement_plugin
- rule_pack
- evidence_graph
- canonical_model
- measurement_result
- exported_files
- published_events
- diagnostics
- execution_metadata
```

The Pipeline Context is immutable between stages.

Each event produces a new Pipeline Context version.

---

# 7. Plugin Architecture

Every extension point is implemented as a plugin.

```
Adapter

Semantic Provider

Measurement Engine

Exporter

Publisher
```

Discovery uses Python Entry Points.

Plugins never communicate directly.

Only the Kernel coordinates them.

---

# 8. Canonical Functional Model

The CFM is the platform contract.

Every downstream component consumes only the CFM.

Never framework documents.

The initial model contains

- Functional Process
- Actor
- Business Entity
- Data Group
- Operation
- Business Rule
- Evidence
- Relationship

---

# 9. Data Flow

```
Markdown

↓

Semantic Facts

↓

Evidence Graph

↓

CFM

↓

Measurement

↓

Result

↓

Export

↓

Telemetry
```

Each stage produces immutable artifacts.

---

# 10. Project Structure

```
specmetrics/

    kernel/

    application/

    sdk/

    plugins/

        adapters/

        semantic/

        measurement/

        exporter/

        publisher/

    cli/

    mcp/

    infrastructure/

    tests/
```

---

# 11. Technology Stack

| Layer           | Technology        |
| --------------- | ----------------- |
| Language        | Python 3.13       |
| Package Manager | uv / pipx         |
| CLI             | Typer             |
| Models          | Pydantic v2       |
| Configuration   | Pydantic Settings |
| Markdown        | markdown-it-py    |
| YAML            | ruamel.yaml       |
| Graph           | NetworkX          |
| LLM Gateway     | LiteLLM           |
| Logging         | structlog         |
| Telemetry       | OpenTelemetry     |
| Testing         | pytest            |

---

# 12. Deployment Model

Release 0.1 supports local execution only.

No centralized server is required.

Execution modes:

- CLI
- MCP Server

Future releases may introduce REST services.

---

# 13. Installation

```
uv tool install specmetrics
```

or

```
pip install specmetrics
```

Optional plugins

```
pip install specmetrics-openspec

pip install specmetrics-speckit

pip install specmetrics-fpa

pip install specmetrics-otel
```

Plugins are automatically discovered.

---

# 14. User Workflows

## CLI

```
specmetrics init

specmetrics measure

specmetrics validate

specmetrics export

specmetrics publish

specmetrics plugins
```

---

## MCP

Available tools

- Measure Specification
- Validate Specification
- Explain Measurement
- Export Measurement
- Search Evidence

---

# 15. Configuration

```
specmetrics.yml
```

Example

```yaml
adapter:
  auto: true

semantic:
  provider: llm

  model: gpt-5

measurement:
  plugin: fpa

publisher:
  - otel

export:
  - json
```

---

# 16. Quality Attributes

| Attribute       | Strategy                          |
| --------------- | --------------------------------- |
| Determinism     | Deterministic measurement engines |
| Traceability    | Evidence Graph                    |
| Explainability  | Evidence-preserving pipeline      |
| Extensibility   | Plugin architecture               |
| Maintainability | Clean Architecture                |
| Scalability     | Independent plugins               |
| Testability     | Immutable pipeline stages         |

---

# 17. Security

The platform adopts a Local-First strategy.

Source code and specifications remain under user control.

Only the Semantic Extraction Provider may require communication with external LLM providers.

Future releases should support:

- local models;
- offline execution;
- encrypted Rule Packs.

---

# 18. Future Evolution

Release 0.1 intentionally establishes the architectural backbone of SpecMetrics.

Future releases are expected to evolve by extending existing contracts rather than modifying the platform core.

Primary evolution paths include:

- new Specification Adapters;
- additional Semantic Providers;
- enterprise Rule Packs;
- new Measurement Engines;
- additional Exporters;
- new Publisher Plugins;
- richer Canonical Functional Model concepts.

The Semantic Measurement Pipeline remains the central execution model throughout the platform's lifecycle.

---

# Appendix A — Execution Sequences

## Purpose

This appendix describes the canonical execution sequences of SpecMetrics Release 0.1.

Each sequence defines how the platform components collaborate to execute the primary use cases of the system.

These sequences are normative and represent the expected runtime behavior of the platform.

---

# ES-01 — Measure Specification

## Goal

Produce a deterministic functional measurement from a Specification Driven Development repository.

## Trigger

```text
specmetrics measure
```

or

```
MCP → Measure Specification
```

---

## Execution Flow

```text
User
 │
 ▼
CLI / MCP
 │
 ▼
Application
 │
 ▼
Pipeline Engine
 │
 │ publish
 ▼
RepositoryLoaded
 │
 ▼
Specification Adapter
 │
 │ publish
 ▼
DocumentsDiscovered
 │
 ▼
Semantic Provider
 │
 │ publish
 ▼
SemanticExtractionCompleted
 │
 ▼
Evidence Graph Builder
 │
 │ publish
 ▼
EvidenceGraphBuilt
 │
 ▼
Canonical Model Builder
 │
 │ publish
 ▼
CanonicalModelBuilt
 │
 ▼
Rule Pack Engine
 │
 │ publish
 ▼
RulePackApplied
 │
 ▼
Measurement Engine
 │
 │ publish
 ▼
MeasurementCompleted
 │
 ├────────► Export Plugins
 │             │
 │             ▼
 │      ExportCompleted
 │
 ├────────► Publisher Plugins
 │             │
 │             ▼
 │     TelemetryPublished
 │
 ▼
PipelineCompleted
 │
 ▼
CLI / MCP
 │
 ▼
User
```

---

## Output

- Canonical Functional Model
- Functional Measurement
- Evidence Graph
- Exported Files
- Published Telemetry

---

## Postconditions

- Measurement completed successfully.
- Traceability preserved.
- Export plugins executed.
- Publisher plugins executed.

---

# ES-02 — Validate Specification

## Goal

Validate semantic consistency before measurement.

## Trigger

```text
specmetrics validate
```

---

## Execution Flow

```text
User
 │
 ▼
CLI / MCP
 │
 ▼
Application
 │
 ▼
Pipeline Engine
 │
 ▼
Specification Adapter
 │
 ▼
Semantic Provider
 │
 ▼
Evidence Graph
 │
 ▼
Semantic Validator
 │
 ▼
Validation Report
```

---

## Validation Rules

The validator shall verify:

- duplicated concepts;
- unresolved references;
- orphan evidence;
- inconsistent relationships;
- missing business actors;
- invalid functional processes.

---

## Output

Validation Report

---

# ES-03 — Explain Measurement

## Goal

Explain how a measurement was produced.

## Trigger

```
MCP → Explain Measurement
```

---

## Execution Flow

```text
User
 │
 ▼
MCP Server
 │
 ▼
Application
 │
 ▼
Measurement Repository
 │
 ▼
Canonical Functional Model
 │
 ▼
Evidence Graph
 │
 ▼
Explanation Generator
 │
 ▼
Human-readable Explanation
```

---

## Output

For each measured function:

- originating specification;
- supporting evidence;
- applied rules;
- measurement methodology;
- final contribution.

---

# ES-04 — Export Measurement

## Goal

Export measurement results.

## Trigger

```text
specmetrics export
```

---

## Execution Flow

```text
Measurement Result
 │
 ▼
Application
 │
 ▼
Export Manager
 │
 ├────────► JSON Plugin
 │
 ├────────► CSV Plugin
 │
 └────────► XML Plugin
 │
 ▼
Generated Files
```

---

## Output

Configured export files.

---

# ES-05 — Publish Measurement

## Goal

Publish engineering telemetry.

## Trigger

```text
specmetrics publish
```

---

## Execution Flow

```text
Measurement Result
 │
 ▼
Application
 │
 ▼
Publisher Manager
 │
 ▼
OpenTelemetry Publisher
 │
 ▼
OpenTelemetry Collector
```

---

## Output

Telemetry Events

---

# ES-06 — Plugin Discovery

## Goal

Discover installed plugins.

## Trigger

Platform startup.

---

## Execution Flow

```text
Kernel
 │
 ▼
Plugin Manager
 │
 ▼
Python Entry Points
 │
 ▼
Plugin Metadata
 │
 ▼
Compatibility Validation
 │
 ▼
Plugin Registry
```

---

## Output

Loaded plugin registry.

---

# ES-07 — Rule Pack Loading

## Goal

Load organizational measurement rules.

---

## Execution Flow

```text
Pipeline Engine
 │
 ▼
Rule Pack Manager
 │
 ▼
Markdown Loader
 │
 ▼
YAML Loader
 │
 ▼
Knowledge Repository
 │
 ▼
Rule Engine
```

---

## Output

Resolved Rule Pack.

---

# ES-08 — MCP Request

## Goal

Execute platform capabilities from AI agents.

---

## Execution Flow

```text
AI Agent
 │
 ▼
MCP Server
 │
 ▼
Application
 │
 ▼
Use Case
 │
 ▼
Pipeline Engine
 │
 ▼
Response
```

---

## Principle

The MCP Server never communicates directly with plugins.

All requests pass through the Application Layer.

---

# ES-09 — Complete Foundation Pipeline

This sequence summarizes the entire Release 0.1 execution model.

```text
Repository
    │
    ▼
Adapter Plugin
    │
    ▼
Semantic Extraction
    │
    ▼
Evidence Graph
    │
    ▼
Canonical Functional Model
    │
    ▼
Rule Pack Engine
    │
    ▼
Measurement Plugin
    │
    ▼
Measurement Result
    │
    ├────────► Export Plugins
    │
    ├────────► Publisher Plugins
    │
    ▼
Engineering Platforms
```

This represents the canonical runtime behavior of the SpecMetrics Foundation architecture.

---

# Sequence Invariants

All execution sequences shall satisfy the following invariants.

| Invariant                       | Description                                                                                                                      |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **SI-01 — Determinism**         | The same inputs, Rule Packs and plugin versions shall always produce identical measurement results.                              |
| **SI-02 — Traceability**        | Every semantic concept shall preserve its originating evidence throughout the entire pipeline.                                   |
| **SI-03 — Canonical Isolation** | Downstream components shall interact exclusively with the Canonical Functional Model.                                            |
| **SI-04 — Plugin Isolation**    | Plugins shall communicate only through the Kernel and public contracts. Direct plugin-to-plugin communication is prohibited.     |
| **SI-05 — Immutable Pipeline**  | Each pipeline stage shall produce immutable outputs. Stages may consume previous artifacts but shall never mutate them in place. |
| **SI-06 — Explainability**      | Every measurement result shall be explainable through semantic evidence and applied rules.                                       |
| **SI-07 — Fail Fast**           | Critical validation errors shall interrupt the pipeline before the Measurement Engine is executed.                               |
| **SI-08 — Idempotence**         | Re-executing the same pipeline with identical inputs shall not introduce side effects beyond regenerating the same outputs.      |
| **SI-09 — Event Ordering**      | Pipeline events shall always be published in the predefined canonical order.                                                     |
| **SI-10 — Immutable Events**    | Published events shall be immutable and may not be modified by subscribers.                                                      |
