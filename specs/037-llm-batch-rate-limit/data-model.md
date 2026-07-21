# Data Model: LLM Batch Processing & Rate Limiting

**Feature**: 037-llm-batch-rate-limit

## Overview

The feature introduces four new internal types and one extension to an existing config model. No changes to the canonical model or semantic element schema.

---

## LLMGateway

Centralized service for all extraction LLM calls. Instantiated once per pipeline run.

| Field | Type | Description |
|-------|------|-------------|
| `config` | `LLMGatewayConfig` | Provider, model, API key, RPM limit |
| `rate_limiter` | `RateLimiter` | Enforces RPM limit for this gateway instance |
| `call_records` | `list[LLMCallRecord]` | Audit log of all calls made through this gateway |

**Methods**:

```
complete(system_prompt: str, user_message: str, json_mode: bool = True) -> str
    Make a single LLM call. Applies rate limiting, retries, JSON mode.
    Returns raw response text.

complete_batch(batch: BatchRequest) -> dict[str, ExtractionResult]
    Send multiple documents in one call. Returns results keyed by document ID.
```

**Lifecycle**: Created at pipeline initialization; shared across extraction stage; discarded after pipeline completes. Call records are logged via structlog.

---

## LLMGatewayConfig

Extension of `LLMProviderConfig` (from `specmetrics/plugins/semantic/llm_provider.py`).

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `provider` | `str` | `"openai"` | Provider identifier (openai, anthropic, gemini, ollama) |
| `model` | `str` | `"gpt-4o-mini"` | Model name string |
| `api_key` | `str \| None` | `None` | API key (redacted in logs) |
| `api_url` | `str \| None` | `None` | Custom API base URL |
| `rpm_limit` | `int` | `15` | Max requests per minute (0 = unlimited) |
| `max_tokens` | `int` | `4096` | Max output tokens per call |
| `max_retries` | `int` | `3` | Max retries for transient failures |
| `batch_max_chars` | `int` | `100000` | Max input characters per batch call |

**Config sources (priority order)**:
1. CLI parameter `--llm-rpm-limit` (overrides rpm_limit only)
2. Environment variable `SPECMETRICS_LLM_RPM_LIMIT`
3. Configuration file `~/.config/specmetrics/config.yml`
4. Default: 15

---

## RateLimiter

Sliding-window rate limiter enforcing requests-per-minute.

| Field | Type | Description |
|-------|------|-------------|
| `rpm_limit` | `int` | Max requests per 60-second window |
| `timestamps` | `deque[float]` | Call timestamps (Unix epoch seconds) |
| `_lock` | `Lock` | Thread safety |

**Methods**:

```
acquire() -> float
    Returns delay in seconds before call can proceed (0.0 if immediate).
    Evicts timestamps > 60s old. If at limit, returns 60 - (now - oldest).

wait_and_record()
    Calls acquire(), sleeps if needed, appends current timestamp.
```

**State machine**: No state transitions. `rpm_limit = 0` means `acquire()` always returns 0.0.

---

## BatchRequest

Groups documents for a single LLM call.

| Field | Type | Description |
|-------|------|-------------|
| `system_prompt` | `str` | Shared system prompt for all documents in batch |
| `documents` | `list[DocumentPayload]` | Document payloads to extract from |
| `json_schema` | `dict \| None` | Expected JSON schema for response validation |

**DocumentPayload**:

| Field | Type | Description |
|-------|------|-------------|
| `document_id` | `str` | Unique ID (from Document.id in the pipeline) |
| `content` | `str` | Document text content (may be a chunk of a larger doc) |
| `document_type` | `str` | e.g., "spec", "plan", "tasks" |

**Prompt Assembly**: The gateway generates:
```
System: {system_prompt}
User:
Document "{doc_id_1}": {content_1}
Document "{doc_id_2}": {content_2}
...
Respond with a JSON object keyed by document ID:
{"{doc_id_1}": {"elements": [...]}, "{doc_id_2}": {"elements": [...]}}
```

**Response Parsing**: `json.loads(response)` → iterate over keys → for each document_id, create `ExtractionResult` from the elements array.

**Validation**: If a document_id from the batch is missing from the response, that document is retried individually. If the response is not valid JSON, the entire batch is retried.

---

## LLMCallRecord

Audit log entry for one LLM call.

| Field | Type | Description |
|-------|------|-------------|
| `call_id` | `str` | UUID for this call |
| `provider` | `str` | Provider used |
| `model` | `str` | Model used |
| `prompt_tokens` | `int` | Input token count (from litellm response) |
| `response_tokens` | `int` | Output token count (from litellm response) |
| `duration_ms` | `int` | Call duration in milliseconds |
| `rate_limit_delay_ms` | `int` | Time spent waiting for rate limiter (0 if no delay) |
| `retry_count` | `int` | Number of retries for this call (0 on first success) |
| `status` | `str` | "success", "failed", "fallback" (used deterministic engine) |
| `error_message` | `str \| None` | Error details if failed |
| `timestamp` | `str` | ISO 8601 timestamp |

**Logging**: Each record is emitted as a structlog event with key `llm_call`. Summary stats (total calls, total tokens, total duration) are logged at pipeline completion.

---

## Relationships

```
PipelineOrchestrator
    └── LLMGateway (1 instance per run)
            ├── RateLimiter (1:1)
            ├── LLMGatewayConfig (1:1)
            └── LLMCallRecord (1:N per run)
                    └── logged via structlog

ExtractionStage
    └── LLMGateway (injected)
            └── complete_batch(BatchRequest) → dict[str, ExtractionResult]

LiteLLMSemanticEngine
    └── LLMGateway (injected)
            └── complete(...) → str

LLMExtractionProvider
    └── LLMGateway (injected)
            └── complete_batch(BatchRequest) → dict[str, ExtractionResult]
```
