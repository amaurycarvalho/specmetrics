# Feature Specification: Measurement Engine Plugin — Business Complexity Points (BCP)

**Feature Branch**: `026-measurement-engine-bcp`

**Created**: 2026-07-17

---

# Clarifications

### Session 2026-07-17

- **Q:** Does the plugin implement the BCP algorithm? → **A:** No. It delegates all Business Complexity Point calculations to the official BCP SDK.
- **Q:** Which SDK SHALL be supported? → **A:** The official `bcp-calculator` Python SDK (`BCPClient`).
- **Q:** Does the plugin perform semantic analysis? → **A:** No. Semantic analysis is delegated to the SDK.
- **Q:** May organizations replace the SDK? → **A:** Yes, provided an adapter implementing the same integration contract is supplied.

---

## Status

Draft

**Input:** User description: "F26"

---

# Overview

The Business Complexity Points (BCP) Measurement Engine is a SpecMetrics Measurement Plugin responsible for integrating the SpecMetrics measurement pipeline with the official **Business Complexity Points (BCP)** calculation engine.

Unlike deterministic measurement engines such as SFP or Story Points, this plugin **does not implement the BCP methodology**.

Instead, it acts as an adapter that:

- extracts measurable work items from the Canonical Functional Model;
- serializes them into the format expected by the official SDK;
- invokes the external BCP Calculator;
- converts the SDK response into the SpecMetrics canonical Measurement Result.

The plugin intentionally delegates all Business Complexity Point logic to the official implementation.

---

# Objectives

The Measurement Engine SHALL:

- integrate with the official BCP SDK;
- avoid reimplementing the BCP methodology;
- preserve complete traceability;
- expose SDK results through the SpecMetrics Measurement API;
- support provider configuration;
- integrate with the Measurement Plugin infrastructure.

---

# User Scenarios & Testing

## User Story 1 — Automatic BCP Measurement (Priority: P1)

A software estimator executes

```bash
specmetrics measure --method bcp
```

The plugin converts the Canonical Functional Model into SDK-compatible stories and calculates Business Complexity Points.

### Acceptance

- SDK executes successfully;
- every processed work item appears in the report;
- SDK output is preserved.

---

## User Story 2 — Explainable Measurement (Priority: P1)

A reviewer wants to understand why a work item received a particular BCP score.

The plugin exposes:

- originating CFM node;
- generated story;
- SDK response;
- component breakdown.

---

## User Story 3 — Provider Configuration (Priority: P2)

An organization wishes to use Claude instead of OpenAI.

The plugin initializes the SDK with the configured provider.

---

## User Story 4 — Pipeline Integration (Priority: P2)

The plugin is automatically discovered and executed after Rule Pack processing.

---

# Edge Cases

- Empty CFM
- Missing Functional Processes
- SDK unavailable
- Invalid provider configuration
- Authentication failure
- SDK timeout
- Rate limiting
- Malformed SDK response
- Missing API credentials
- Partial batch failures

---

# Constitution Check

## Principle IV — Deterministic Execution

Not Applicable.

BCP calculations are delegated to an external LLM-based SDK and therefore are not guaranteed to be deterministic.

---

## Principle VI — Explainability

Satisfied.

The plugin preserves all evidence returned by the SDK.

---

## Principle VII — Canonical Representation

Satisfied.

The plugin consumes only the Canonical Functional Model.

---

## Principle VIII — Plugin Architecture

Satisfied.

Plugin is discovered through Entry Points.

---

## Principle IX — Rule Externalization

Satisfied.

SDK configuration is externalized.

---

# Functional Requirements

## General

### FR-001

The Measurement Engine SHALL consume only the Canonical Functional Model.

---

### FR-002

The engine SHALL delegate Business Complexity Point calculation to the official BCP SDK.

---

### FR-003

The engine SHALL NOT implement BCP scoring logic.

---

### FR-004

The engine SHALL preserve evidence references.

---

### FR-005

The engine SHALL expose machine-readable output.

---

### FR-006

The engine SHALL execute as a discoverable Measurement Plugin.

---

### FR-007

The engine SHALL support pipeline execution.

---

### FR-008

The engine SHALL complete processing whenever recoverable SDK warnings occur.

---

# Story Generation

### FR-009

Each Functional Process SHALL be converted into a story representation compatible with the BCP SDK.

---

### FR-010

Story generation SHALL preserve links to originating CFM nodes.

---

### FR-011

Generated stories SHALL include sufficient business context for BCP evaluation.

---

### FR-012

The generated story SHALL be preserved as measurement evidence.

---

# SDK Integration

### FR-013

The plugin SHALL instantiate `BCPClient`.

---

### FR-014

The plugin SHALL support SDK provider configuration.

---

### FR-015

Supported providers SHALL include:

- OpenAI
- Claude

---

### FR-016

The plugin SHALL invoke:

```python
client.calculate(story_content)
```

for each generated story.

---

### FR-017

Batch execution MAY invoke:

```python
client.batch_calculate(...)
```

when supported by the execution strategy.

---

### FR-018

Provider comparison MAY invoke:

```python
client.compare_providers(...)
```

when explicitly requested.

---

### FR-019

SDK exceptions SHALL be translated into Measurement Engine errors.

---

### FR-020

The plugin SHALL NOT modify SDK scoring results.

---

# Rule Packs

### FR-021

Rule Packs MAY customize story generation.

---

### FR-022

Rule Packs MAY customize SDK provider selection.

---

### FR-023

Rule Packs SHALL NOT alter SDK calculation results.

---

### FR-024

All Rule Pack adjustments SHALL be reported.

---

# Explainability

### FR-025

Every measured work item SHALL expose:

- originating CFM node;
- generated story;
- SDK provider;
- SDK breakdown;
- total BCP.

---

### FR-026

SDK responses SHALL be preserved as immutable evidence.

---

### FR-027

Evidence SHALL survive export.

---

# Pipeline

### FR-028

Pipeline execution order SHALL be:

```text
Semantic Extraction

↓

Canonical Functional Model

↓

Rule Pack Engine

↓

BCP Measurement Engine

↓

Official BCP SDK

↓

Export Layer
```

---

### FR-029

The Measurement Engine SHALL emit Measurement Events.

---

### FR-030

The plugin SHALL support asynchronous execution.

---

### FR-031

The plugin SHALL support incremental execution.

---

### FR-032

Only modified Functional Processes SHALL be re-submitted to the SDK.

---

# Measurement Result

The output SHALL include:

```text
Measurement Method

SDK Version

Provider

Measurement Timestamp

Measured Work Items

Component Breakdown

Total BCP

Applied Rule Packs

Evidence References

Warnings

Execution Statistics
```

---

# Key Entities

## BCP Measurement Result

Complete SDK measurement output.

---

## Generated Story

Story produced from the Canonical Functional Model.

---

## SDK Result

Business Complexity Point response returned by the official SDK.

---

## Measurement Evidence

Complete traceability linking CFM, generated story and SDK output.

---

## Rule Pack

External policy modifying integration behavior.

---

# Plugin Interfaces

```text
MeasurementPlugin

measure()

validate()

describe()

supported_methods()

version()
```

---

# Output Example

```json
{
  "method": "BCP",
  "sdk": "bcp-calculator",
  "provider": "openai",
  "measured_items": 24,
  "total_bcp": 178,
  "warnings": [],
  "rule_pack": "default",
  "explainability": []
}
```

---

# Observability

### FR-033

The engine SHALL emit structured INFO and ERROR log messages for SDK initialization, story submission, SDK completion and failures.

---

### FR-034

The engine SHALL emit OpenTelemetry metrics including:

- SDK execution duration histogram;
- processed story gauge;
- SDK request counter;
- SDK error counter.

---

# Success Criteria

## SC-001

100% of measured work items SHALL preserve traceability between CFM, generated story and SDK result.

---

## SC-002

100% of SDK responses SHALL be preserved without modification.

---

## SC-003

The plugin SHALL automatically discover the official SDK when installed.

---

## SC-004

Incremental execution SHALL submit only modified Functional Processes.

---

## SC-005

Provider configuration SHALL be externalized.

---

## SC-006

SDK failures affecting individual stories SHALL not prevent processing of remaining stories whenever batch execution is supported.

---

## SC-007

The plugin SHALL remain compatible with future SDK versions through the adapter interface, provided backward compatibility is maintained by the SDK.

---

# Non-Goals

The plugin does **not**:

- implement the BCP methodology;
- reproduce the BCP scoring algorithm;
- perform independent Business Complexity Point calculations;
- replace the official SDK;
- invoke LLMs directly;
- parse source code;
- perform semantic extraction.

---

# Assumptions

- The Canonical Functional Model has already been validated.
- The official `bcp-calculator` SDK is installed and available.
- API credentials have been configured for the selected provider.
- Rule Packs have been resolved before measurement.
- Export plugins consume Measurement Results.
- The BCP SDK remains the authoritative implementation of the Business Complexity Points methodology.

---

# Implementation Notes

The BCP Measurement Engine is intentionally designed as a **thin integration layer** rather than a measurement algorithm. Its responsibility is to bridge the SpecMetrics Canonical Functional Model with the official Business Complexity Points ecosystem while preserving the architectural principles of the platform. By delegating all scoring decisions to the external SDK, the plugin automatically benefits from future improvements, methodological refinements and provider enhancements without requiring changes to SpecMetrics itself. This adapter-based approach keeps the platform vendor-neutral, minimizes maintenance effort and ensures that organizations always execute the canonical implementation of the BCP methodology.

> **Note:** This specification intentionally defines the **plugin architecture, SDK integration contract, explainability model, pipeline behavior and interoperability requirements** for Business Complexity Points. It explicitly excludes any reimplementation of the proprietary BCP calculation methodology, treating the official `bcp-calculator` SDK as the single authoritative source for Business Complexity Point computation.
