# Implementation Plan: Measurement Engine Plugin — Business Complexity Points (BCP)

**Branch**: `026-measurement-engine-bcp` | **Date**: 2026-07-17 | **Spec**: `specs/026-measurement-engine-bcp/spec.md`

**Input**: Feature specification from `specs/026-measurement-engine-bcp/spec.md`

## Summary

Implement a BCP measurement engine plugin that acts as an adapter between the SpecMetrics pipeline and the official `bcp-calculator` Python SDK. The plugin converts CFM Functional Processes into markdown user stories, submits them to `BCPClient.calculate()`, collects the `total_bcp` + `breakdown` response, and wraps results in the standard Measurement Result format. Retries with exponential backoff on transient SDK failures; returns empty result with warnings when SDK is unavailable.

## Technical Context

**Language/Version**: Python >=3.12

**Primary Dependencies**: Pydantic v2 (models), `bcp-calculator` SDK (external), structlog (logging), `python-dotenv` (environment loading)

**Storage**: In-memory measurement; SDK call results not persisted

**Testing**: pytest with `unittest.mock` for SDK mocking

**Target Platform**: Linux — CLI + MCP Server (requires API credentials for external SDK)

**Project Type**: Library/CLI — Measurement Engine Plugin (adapter pattern wrapping external SDK)

**Performance Goals**: N/A (SDK call latency dominated by LLM inference; plugin overhead negligible)

**Constraints**: Non-deterministic (delegates to LLM-based SDK), requires `.env` with API keys, SDK MUST be installed separately, no independent BCP scoring logic, retry per-item with exponential backoff (3 attempts)

**Scale/Scope**: 500+ Functional Processes per run; each process → SDK call → response mapping

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: V (Evidence First), VII (Canonical Representation), VIII (Plugin-Oriented), IX (Rule Externalization), X (AI-Friendly by Design), XI (Observability), XII (Open by Default)

**Compliance Verifications**:
- [x] Evidence First (V): Every BCPWorkItem preserves generated story, SDK response, and CFM evidence references (FR-004, FR-025). SDK responses are immutable evidence (FR-026).
- [x] Canonical Representation (VII): Consumes only the Canonical Functional Model (FR-001). No framework-specific artifacts.
- [x] Plugin-Oriented (VIII): Implemented as a Measurement Engine plugin discovered via Entry Points (FR-006, SC-005).
- [x] Rule Externalization (IX): Story generation and provider selection are customizable via Rule Packs (FR-021–FR-025).
- [x] AI-Friendly by Design (X): Output is machine-readable JSON (FR-005), consumable by AI agents.
- [x] Observability (XI): Emits structured logs (FR-034) and OpenTelemetry metrics (FR-035) including SDK duration histogram and request/error counters.
- [x] Open by Default (XII): Plugin interface and SDK adapter contract are documented. Organizations can replace the SDK via the adapter protocol.
- [ ] ~~Principle IV (Deterministic Execution)~~: Not Applicable — BCP calculation is delegated to an external LLM-based SDK. Stated explicitly in spec Constitution Check.

## Project Structure

### Documentation (this feature)

```text
specs/026-measurement-engine-bcp/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
specmetrics/plugins/measurement/bcp/           # New measurement plugin
├── __init__.py
├── plugin.py                       # BCPPlugin, BCPHandler, create_metadata()
├── models.py                       # BCPMeasurementResult, GeneratedStory, BCPWorkItem,
#                                   # SDKResult, MeasurementEvidence
├── story_generator.py              # CFM → markdown user story string conversion
├── sdk_adapter.py                  # BCPClient wrapper with retry, error translation
└── explainer.py                    # Explainability per FR-026

tests/
├── unit/
│   ├── test_bcp_story_generator.py      # CFM → story conversion
│   ├── test_bcp_sdk_adapter.py          # Retry, error handling, provider config
│   ├── test_bcp_models.py              # Model construction, serialization
│   └── test_bcp_integration.py         # Mock SDK → full measurement flow
├── contract/
│   └── test_bcp_measurement.py         # Measurement API contract
└── integration/
    └── test_bcp_pipeline.py            # Full pipeline with mocked SDK
```

**Structure Decision**: Follows existing measurement plugin convention. Dedicated `story_generator.py` for CFM→markdown conversion and `sdk_adapter.py` for BCPClient wrapping/retry.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Non-deterministic (Principle IV) | The BCP methodology is defined by an external LLM-based SDK; SpecMetrics cannot enforce determinism on a third-party service | Skipping BCP support entirely — rejected because BCP is a requested enterprise methodology |
