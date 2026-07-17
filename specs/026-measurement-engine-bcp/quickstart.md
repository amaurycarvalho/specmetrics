# Quickstart: Business Complexity Points (BCP) Measurement Engine

## Prerequisites

- Python >= 3.12 with `uv` or `pipx`
- Clone of `specmetrics` at branch `026-measurement-engine-bcp`
- `bcp-calculator` SDK installed: `pip install bcp-calculator`
- `.env` file configured with API keys: `OPENAI_API_KEY` and/or `ANTHROPIC_API_KEY`
- Dependencies installed: `uv sync` (or `pip install -e ".[dev]"`)

## Setup

```bash
# From repo root
uv sync
cp .env.example .env   # Edit with your API keys
```

## Validation Scenarios

### Scenario 1: Story generation from CFM

```bash
pytest tests/unit/test_bcp_story_generator.py -v
```

**Expected**: Each Functional Process generates a markdown user story string. Story includes title, description, actors, operations, business rules, data groups.

**Data model reference**: `specs/026-measurement-engine-bcp/data-model.md`

### Scenario 2: SDK adapter with mock

```bash
pytest tests/unit/test_bcp_sdk_adapter.py -v
```

**Expected**: Adapter calls `BCPClient.calculate()` with story string. Returns parsed `total_bcp` + `breakdown`. Retries on transient failures. Auth failures fail immediately.

### Scenario 3: Full measurement flow with mock SDK

```bash
pytest tests/unit/test_bcp_integration.py -v
```

**Expected**: Known CFM → generated stories → mock SDK → BCPMeasurementResult with correct per-item scores and total.

### Scenario 4: Missing SDK gracefully degrades

```bash
pytest tests/unit/test_bcp_integration.py -v -k test_missing_sdk
```

**Expected**: When `bcp-calculator` is not installed, engine returns empty result with warnings. Pipeline continues.

### Scenario 5: Partial batch failure

```bash
pytest tests/unit/test_bcp_sdk_adapter.py -v -k test_partial_failure
```

**Expected**: Some items fail, others succeed. Failed items have `status == "failed"`. `total_bcp` reflects only successful items.

### Scenario 6: Full pipeline integration

```bash
pytest tests/integration/test_bcp_pipeline.py -v
```

**Expected**: Pipeline executes CFM → BCP measurement with mocked SDK. Result contains per-item breakdown and total.

## Key Contracts

| Artifact | Path |
|----------|------|
| Data model | `specs/026-measurement-engine-bcp/data-model.md` |
| Measurement API | `specs/026-measurement-engine-bcp/contracts/measurement-api.md` |
| Spec | `specs/026-measurement-engine-bcp/spec.md` |
