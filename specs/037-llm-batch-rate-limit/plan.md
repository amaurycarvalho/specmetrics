# Implementation Plan: LLM Batch Processing & Rate Limiting

**Branch**: `037-llm-batch-rate-limit` | **Date**: 2026-07-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/037-llm-batch-rate-limit/spec.md`

## Summary

Optimize SpecMetrics' LLM integration by introducing a unified gateway with batch processing (multiple documents per call), configurable rate limiting (default 15 RPM), and universal JSON structured output mode. Reduces total LLM call count by 50%+ via batching, prevents provider rate-limit errors via throttling, and eliminates fragile response parsing via JSON mode.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: LiteLLM (already in pyproject.toml), Pydantic v2 (models for gateway config/responses), structlog (call logging)

**Storage**: In-memory (rate limiter timestamps, batch state); no persistent storage needed

**Testing**: pytest

**Target Platform**: Linux (CLI)

**Project Type**: CLI tool extension (kernel-level infrastructure)

**Performance Goals**: 50% reduction in LLM call count via batching (SC-001); rate-limited pacing within configured RPM (SC-002); zero response preprocessing needed (SC-003)

**Constraints**: Per-process rate limiting (no cross-process coordination); max 3 retries with exponential backoff; backward compatibility when rate limit is disabled (0)

**Scale/Scope**: Two extraction systems migrated to gateway (`LiteLLMSemanticEngine`, `LLMExtractionProvider`); BCP SDK and CLI test excluded; ~30-45 calls per run reduced to ~2-5

## Constitution Check

*GATE: Must pass before Phase 0 research.*

**Engaged Principles**:
- Principle IV (LLM-Assisted, Deterministic Results): Gateway optimizes LLM calls without changing what the LLM extracts
- Principle VIII (Plugin-Oriented Architecture): Gateway is a kernel-level service consumed by plugins
- Principle X (AI-Friendly by Design): Lower cost and reliable rate limiting make the platform more practical
- Principle XIII (Evolution Without Disruption): Batching and JSON mode are additive; same extraction output format
- Principle XIV (Layer Independence): Gateway at kernel/infrastructure boundary, stable abstraction over provider SDKs

**Compliance Verifications**:
- [x] Specification First: Extraction consumes software specifications (unchanged)
- [x] Evidence First: Evidence references preserved (same element schema, same attribution)
- [x] Canonical Representation: Gateway operates on Document objects; extraction output flows to CSM/CFM unchanged
- [x] Plugin-Oriented: Gateway is a kernel service; extraction plugins consume it via dependency injection
- [x] Rule Externalization: N/A — no new counting rules
- [x] Layer Independence: Gateway exposes LLMCompletionProtocol; providers depend on gateway, not the reverse
- [x] Open by Default: Gateway interface documented in this plan; rate limit configurable via standard env vars

## Project Structure

### Documentation (this feature)

```text
specs/037-llm-batch-rate-limit/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
specmetrics/
├── kernel/
│   ├── llm_gateway.py           # NEW: LLMGateway, RateLimiter, BatchBuilder, LLMCallRecord
│   ├── litellm_engine.py        # MODIFY: delegate _call_llm() to gateway
│   └── semantic_extraction_engine.py  # MODIFY: inject gateway into engine factory
├── plugins/
│   └── semantic/
│       └── llm_provider.py      # MODIFY: delegate litellm.completion() to gateway
├── application/
│   └── orchestrator.py          # MODIFY: extract LLM call stats from gateway for PipelineResult
├── cli/
│   ├── app.py                   # MODIFY: add --llm-rpm-limit parameter to measure command
│   └── measure.py               # MODIFY: pass rpm_limit to pipeline request
└── tests/
    └── test_llm_gateway.py      # NEW: unit tests for gateway, rate limiter, batch building
```

**Structure Decision**: Gateway lives in `kernel/` as a core service — consistent with constitution principle VIII (kernel coordinates plugins). Rate limiter and batch builder are internal classes used by the gateway. No new directories needed.

## Complexity Tracking

> No constitution violations to justify.

## Design Decisions

### 1. Gateway Location

**Decision**: Place `LLMGateway` in `specmetrics/kernel/llm_gateway.py`. The kernel layer coordinates plugins; a gateway is a coordination service. Extraction providers (semantic plugins) depend on the gateway, not the reverse, satisfying Layer Independence.

### 2. Batch Prompt Assembly

**Decision**: The `BatchBuilder` takes a list of `Document` objects, constructs a numbered list prompt, and parses the JSON object response (keyed by document ID) back into per-document element lists. Template:
```
System: Extract semantic elements from the following documents...
User:
Document "doc-1": <content>
Document "doc-2": <content>
Respond as: {"doc-1": {"elements": [...]}, "doc-2": {"elements": [...]}}
```

### 3. Rate Limiter Algorithm

**Decision**: Sliding window rate limiter. Maintains a deque of call timestamps. Before each call, evicts entries older than 60 seconds. If `len(timestamps) >= rpm_limit`, computes delay = 60 - (now - oldest_timestamp) and sleeps. Thread-safe via a lock.

### 4. JSON Mode Enforcement

**Decision**: Gateway always passes `response_format={"type": "json_object"}` to litellm (for OpenAI-compatible providers). For non-OpenAI providers, appends "Respond with valid JSON only. No markdown fences." to the system prompt. Response validation: attempt `json.loads()`, retry once with corrected prompt on failure, fall back to deterministic extraction after max retries.

### 5. Migration Strategy

Both extraction systems migrate independently but share the same gateway instance:
- `LiteLLMSemanticEngine._call_llm()` → replaced by `gateway.complete()`
- `LLMExtractionProvider.extract()` → chunk loop replaced by `gateway.complete_batch()`
- Gateway instance created once at pipeline initialization, injected into extraction stage
