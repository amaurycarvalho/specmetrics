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
- **Q:** What format should generated stories use for the BCP SDK? → **A:** Markdown user story narrative text (not JSON). The SDK's `calculate()` method accepts `story_content: str`.
- **Q:** What attributes should BCPMeasurementResult and SDKResult have? → **A:** BCPMeasurementResult with per-item breakdown, total, provider, SDK version; SDKResult with raw response, status, provider, duration.
- **Q:** What retry strategy should be used for SDK timeouts and rate limits? → **A:** Retry per-item with exponential backoff (3 attempts), skip on persistent failure, continue batch.

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
- SDK timeout — retry per-item with exponential backoff (3 attempts), skip item and continue on persistent failure
- Rate limiting — retry per-item with exponential backoff (3 attempts), skip item and continue on persistent failure
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

Generated stories SHALL include sufficient business context for BCP evaluation, formatted as a markdown user story string with the following sections populated from CFM data:

- **Title**: `# User Story: {Functional Process name}`
- **Description**: `As a {actor}, I want to {description}, so that...`
- **Acceptance Criteria**: Bullet list derived from related operations, business rules, data groups, and relationships
- **Context**: Supporting information about related actors, constraints, data groups, and business rules

Example generated story string:

```markdown
# User Story: Process Order

As a customer, I want to process an order, so that I can receive purchased items.

## Acceptance Criteria:
1. System validates order against inventory (business rule: stock_validation)
2. System notifies shipping department (operation: notify_shipping)
3. Order record is created in orders database (data group: orders)
4. Payment is processed through payment gateway (relationship: communicates_with)
```

---

### FR-012

The generated story SHALL be preserved as measurement evidence.

---

# SDK Integration

### FR-013

The plugin SHALL instantiate `BCPClient` with configurable parameters:

```python
from src.sdk import BCPClient

client = BCPClient(
    log_level="INFO",    # DEBUG, INFO, WARNING, ERROR, CRITICAL
    provider="openai",   # "openai" or "claude" — defaults to "openai"
)
```

---

### FR-014

The plugin SHALL support SDK provider configuration via Rule Packs or external configuration.

---

### FR-015

Supported providers SHALL include:

- OpenAI
- Claude

---

### FR-016

The plugin SHALL invoke `client.calculate(story_content: str)` for each generated story.

The method accepts a **markdown string** and returns:

```python
{
    "total_bcp": float,        # Total Business Complexity Points
    "breakdown": {             # Per-component breakdown
        "component_name": float,
        ...
    }
}
```

---

### FR-017

For in-memory story generation, the plugin SHALL invoke `client.calculate()` individually for each story in a loop. The SDK's `batch_calculate()` method is designed for file-directory processing (reads `*.md` files from a directory) and MAY be used by optionally writing stories to temporary files first.

SDK signature for reference:

```python
batch_calculate(
    stories_dir: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    file_pattern: str = "*.md"
) -> Dict[str, Dict[str, Any]]
```

---

### FR-018

Provider comparison MAY invoke:

```python
client.compare_providers(
    story_content: str,
    providers: Optional[List[str]] = None   # defaults to ["openai", "claude"]
)
```

when explicitly requested. The default providers list is `["openai", "claude"]`.

---

### FR-019

The plugin SHALL verify that the required API credentials are available before invoking the SDK. Credentials are loaded by the SDK from a `.env` file containing provider API keys (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`).

---

### FR-020

SDK exceptions SHALL be translated into Measurement Engine errors.

---

### FR-021

The plugin SHALL NOT modify SDK scoring results.

---

# Rule Packs

### FR-022

Rule Packs MAY customize story generation.

---

### FR-023

Rule Packs MAY customize SDK provider selection.

---

### FR-024

Rule Packs SHALL NOT alter SDK calculation results.

---

### FR-025

All Rule Pack adjustments SHALL be reported.

---

# Explainability

### FR-026

Every measured work item SHALL expose:

- originating CFM node;
- generated story;
- SDK provider;
- SDK breakdown;
- total BCP.

---

### FR-027

SDK responses SHALL be preserved as immutable evidence.

---

### FR-028

Evidence SHALL survive export.

---

# Pipeline

### FR-029

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

### FR-030

The Measurement Engine SHALL emit Measurement Events.

---

### FR-031

The plugin SHALL support asynchronous execution.

---

### FR-032

The plugin SHALL support incremental execution.

---

### FR-033

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

## BCPMeasurementResult

Complete SDK measurement output identified by pipeline run ID.

Contains:
- **method**: "BCP"
- **provider**: SDK provider used (e.g., "openai", "claude")
- **sdk_version**: Version of the bcp-calculator SDK
- **items**: List of per-work-item BCP results
- **total_bcp**: Sum of all item scores
- **generated_stories**: List of GeneratedStory objects
- **applied_rule_pack**: Rule Pack identifier
- **warnings**: Non-fatal issues
- **execution_metadata**: Timing, counts, SDK call metrics

---

## GeneratedStory

Story produced from the Canonical Functional Model. Serialized as a markdown user story string for the SDK.

Contains:
- **content**: The markdown user story string (title, description, acceptance criteria, context)
- **evidence_ref**: Link to originating CFM node

---

## BCPWorkItem

Per-work-item measurement result from the SDK.

Contains:
- **element_id**: UUID of the originating Functional Process
- **element_name**: Functional Process name
- **generated_story**: The GeneratedStory submitted to the SDK
- **sdk_response**: Raw SDK response for this item
- **bcp_score**: Business Complexity Point score
- **component_breakdown**: SDK-provided breakdown (if available)
- **evidence_refs**: Traceability links

---

## SDKResult

Business Complexity Point response returned by the official SDK. The SDK's `client.calculate()` returns `Dict[str, Any]` with the following structure.

Contains:
- **total_bcp**: Total Business Complexity Points (float)
- **breakdown**: Per-component breakdown of points (dict of component_name → points)
- **raw_response**: Complete SDK response payload (dict)
- **provider**: Provider that processed this request
- **duration_ms**: SDK execution time
- **warnings**: SDK-generated warnings
- **errors**: SDK-generated errors

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
  "sdk_version": "1.0.0",
  "provider": "openai",
  "measured_items": 3,
  "total_bcp": 47.5,
  "distribution": {},
  "items": [
    {
      "element_id": "fp-001",
      "element_name": "Process Order",
      "generated_story": "# User Story: Process Order\n\nAs a customer...",
      "sdk_response": {
        "total_bcp": 18.0,
        "breakdown": {
          "business_logic": 8.0,
          "data_complexity": 5.0,
          "integration": 3.0,
          "rules": 2.0
        }
      },
      "bcp_score": 18.0,
      "component_breakdown": {
        "business_logic": 8.0,
        "data_complexity": 5.0,
        "integration": 3.0,
        "rules": 2.0
      },
      "evidence_refs": [
        {"element_id": "fp-001", "document_id": "spec.md", "story_point_value": 8}
      ]
    }
  ],
  "warnings": [],
  "rule_pack": "default",
  "execution_metadata": {
    "duration_ms": 2450,
    "total_fps_processed": 3,
    "sdk_call_count": 3,
    "version": "1.0"
  }
}
```

---

# Observability

### FR-034

The engine SHALL emit structured INFO and ERROR log messages for SDK initialization, story submission, SDK completion and failures.

---

### FR-035

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

# SDK Integration Reference

## Package

```
pip install bcp-calculator
```

Import: `from src.sdk import BCPClient`

**Note:** The import path uses `src.sdk` from a local install or `bcp_calculator` from the published package. The plugin MUST handle both import paths or use a discovery mechanism.

## Constructor

```python
BCPClient(
    log_level: str = "INFO",    # DEBUG, INFO, WARNING, ERROR, CRITICAL
    provider: str = "openai",   # "openai" or "claude"
)
```

## Methods

| Method | Input | Returns |
|--------|-------|---------|
| `calculate(story_content)` | `str` — markdown user story | `Dict[str, Any]` — `{"total_bcp": float, "breakdown": dict}` |
| `calculate_file(file_path)` | `str` or `Path` — file path | `Dict[str, Any]` — same as `calculate()` |
| `batch_calculate(stories_dir, output_path, file_pattern)` | Directory path, optional output path, glob pattern `"*.md"` | `Dict[str, Dict[str, Any]]` — filename → result |
| `compare_providers(story_content, providers)` | Story string, optional provider list (default `["openai", "claude"]`) | `Dict[str, Dict[str, Any]]` — provider → result |

## Return Format (calculate)

```json
{
  "total_bcp": 18.0,
  "breakdown": {
    "business_logic": 8.0,
    "data_complexity": 5.0,
    "integration": 3.0,
    "rules": 2.0
  }
}
```

## Environment Setup

The SDK loads API credentials from a `.env` file at the project root or working directory:

```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## Error Handling

- `calculate()` raises SDK-specific exceptions on API failure, authentication failure, or malformed response
- `calculate_file()` raises `FileNotFoundError` if the file does not exist
- `batch_calculate()` raises `NotADirectoryError` if the directory does not exist

## Adapter Contract

Organizations replacing the SDK (per clarification) MUST implement a compatible adapter with:

```python
class BCPAdapter(Protocol):
    def calculate(self, story_content: str) -> dict[str, Any]: ...
    def calculate_file(self, file_path: str | Path) -> dict[str, Any]: ...
    def batch_calculate(
        self,
        stories_dir: str | Path,
        output_path: str | Path | None = None,
        file_pattern: str = "*.md",
    ) -> dict[str, dict[str, Any]]: ...
    def compare_providers(
        self,
        story_content: str,
        providers: list[str] | None = None,
    ) -> dict[str, dict[str, Any]]: ...
```

---

# Implementation Notes

The BCP Measurement Engine is intentionally designed as a **thin integration layer** rather than a measurement algorithm. Its responsibility is to bridge the SpecMetrics Canonical Functional Model with the official Business Complexity Points ecosystem while preserving the architectural principles of the platform. By delegating all scoring decisions to the external SDK, the plugin automatically benefits from future improvements, methodological refinements and provider enhancements without requiring changes to SpecMetrics itself. This adapter-based approach keeps the platform vendor-neutral, minimizes maintenance effort and ensures that organizations always execute the canonical implementation of the BCP methodology.

> **Note:** This specification intentionally defines the **plugin architecture, SDK integration contract, explainability model, pipeline behavior and interoperability requirements** for Business Complexity Points. It explicitly excludes any reimplementation of the proprietary BCP calculation methodology, treating the official `bcp-calculator` SDK as the single authoritative source for Business Complexity Point computation.
