# Research: LLM Batch Processing & Rate Limiting

**Feature**: 037-llm-batch-rate-limit
**Date**: 2026-07-21

## Research Task 1: Current LLM Call Inventory

### Finding

Four call sites exist in the codebase:

| # | File | Line | System | Batch? | JSON Mode? | Rate Limit? |
|---|------|------|--------|--------|------------|-------------|
| 1 | `kernel/litellm_engine.py` | 77 | LiteLLMSemanticEngine | No (per-doc) | Yes | No |
| 2 | `plugins/semantic/llm_provider.py` | 267 | LLMExtractionProvider | No (per-chunk) | No | Partial (3 retries) |
| 3 | `cli/config_commands.py` | 328 | CLI test | N/A | No | No |
| 4 | `plugins/measurement/bcp/sdk_adapter.py` | 106 | BCP SDK | No (per-FP) | N/A | No (3 retries) |

In-scope for gateway: #1 and #2 (both extraction). Out-of-scope: #3 (test-only), #4 (BCP, excluded per clarification).

Both in-scope systems process documents sequentially — one LLM call per document (LiteLLM) or one per chunk (LLMExtractionProvider with 8K chunk size). Typical run: 10 documents × 3 chunks + 5 BCP processes = 35-45 LLM calls.

### Decision

Gateway unifies #1 and #2. Both systems delegate to `gateway.complete()` for individual calls. The extraction stage uses `gateway.complete_batch()` to group documents. BCP and CLI test remain unchanged.

### Alternatives Considered

- **Gateway all 4 call sites**: Rejected — BCP SDK is a black box; CLI test is trivial and doesn't need rate limiting.
- **Remove LiteLLMSemanticEngine**: Rejected — existing configurations may reference it; migrate rather than remove.

---

## Research Task 2: LiteLLM JSON Mode Support

### Finding

LiteLLM supports `response_format={"type": "json_object"}` for OpenAI, Azure, and compatible providers. The parameter is passed through directly. For Anthropic (Claude), Gemini, and other non-OpenAI providers, JSON mode is not natively supported — LiteLLM translates the request or the parameter is ignored.

The existing `LiteLLMSemanticEngine` already uses `response_format={"type": "json_object"}` (line 77 of litellm_engine.py) and it works for OpenAI providers. The `LLMExtractionProvider` does NOT set this parameter (line 267 of llm_provider.py), requiring `_strip_code_fence()` to clean responses.

### Decision

Gateway applies `response_format={"type": "json_object"}` universally for OpenAI-compatible providers. Provider type is detected from the model string (prefix-based heuristics: `gpt-` → OpenAI, `claude-` → Anthropic, `gemini-` → Google). For non-OpenAI providers, gateway falls back to prompt-based JSON instructions + response cleaning.

### Alternatives Considered

- **Detect via litellm API**: LiteLLM does not expose a clean API to query provider capabilities at runtime.
- **User-configurable JSON mode toggle**: Over-engineering; default behavior is correct for 90%+ of users.

---

## Research Task 3: Rate Limiter Design Patterns

### Finding

Three common rate limiter algorithms:

1. **Token bucket**: Tokens replenish at configured rate; each call consumes one token. Good for burst handling.
2. **Sliding window**: Timestamps deque; count calls in last 60s. Simple, accurate, no token replenishment complexity.
3. **Leaky bucket**: Fixed-size queue; requests are dequeued at constant rate. Oversize queue drops requests.

For a CLI tool, the sliding window is ideal: simple to implement, accurate RPM enforcement, and no burst-handling complexity needed (CLI pipeline is sequential).

### Decision

Sliding window approach using `collections.deque`. Before each call: evict timestamps older than 60s, if count >= limit, sleep for `60 - (now - oldest)`. Thread-safe via `threading.Lock`.

### Alternatives Considered

- **Token bucket with burst**: Unnecessary complexity for a sequential pipeline.
- **External library (ratelimit, limits)**: Adds dependency; sliding window is ~20 lines of code.
- **Asyncio-based**: Pipeline is synchronous (Typer CLI); async adds complexity without parallelism benefit.

---

## Research Task 4: Batch Size Heuristics

### Finding

GPT-4 context window: 128K tokens. GPT-4o-mini: 128K tokens. Typical specification document: 500-2000 tokens. With 10 documents at 1000 tokens each + prompt overhead (~500 tokens) = ~10.5K tokens — well within context window.

The `LLMExtractionProvider` chunks at 8000 characters (~2000 tokens). With batching, the chunk size can increase since multiple documents share prompt overhead, but the constraint is output token limit (max_tokens parameter) rather than input context.

For batched responses, the LLM must output JSON for all documents. A batch of 5 documents requires roughly 5× the output tokens of a single document. Conservative estimate: 4096 output tokens per call.

### Decision

Batch size target: fit as many documents as possible within input context (128K tokens), using conservative estimate of 4 chars ≈ 1 token. Default max batch chars: 100,000 (≈25K tokens), leaving headroom for prompt + response. Documents exceeding the batch limit are chunked internally (within `LLMExtractionProvider`'s existing chunking logic).

### Alternatives Considered

- **Fixed document count (e.g., 5 docs per batch)**: Too rigid; large documents would exceed context, small docs would waste capacity.
- **Token-counting library (tiktoken)**: Adds dependency; character-based heuristic is sufficient (4 chars ≈ 1 token is a standard approximation).

---

## Research Task 5: Provider Configuration Mapping

### Finding

The `LLMExtractionProvider` discovers provider configuration from: constructor args → YAML config file → environment variables. The `LiteLLMSemanticEngine` uses a simpler model string passed via `SemanticEngineFactory`. These need to converge on a single configuration source for the gateway.

### Decision

Gateway reads configuration from the existing `LLMProviderConfig` model (used by `LLMExtractionProvider`), extended with `rpm_limit: int = 15`. The `SemanticEngineFactory` is updated to pass its model/provider to the gateway's config. Environment variable `SPECMETRICS_LLM_RPM_LIMIT` overrides the config file default.

### Alternatives Considered

- **New separate config system for gateway**: Rejected — duplicates existing config infrastructure.
- **Gateway reads from multiple sources inconsistently**: Rejected — single source of truth needed for consistent rate limiting.
