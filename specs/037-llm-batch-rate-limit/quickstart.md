# Quickstart: LLM Batch Processing & Rate Limiting

**Feature**: 037-llm-batch-rate-limit

## Prerequisites

- Python 3.13+ with `specmetrics` installed (development mode: `pip install -e .`)
- A valid LLM API key configured (env var or config file)
- A project directory with multiple specification files (at least 3 documents)

## Validation Scenarios

### Scenario 1: Gateway Unifies Both Extraction Systems

**Purpose**: Verify both `LiteLLMSemanticEngine` and `LLMExtractionProvider` route calls through the gateway.

```bash
# Check: no litellm.completion() calls outside gateway in kernel/litellm_engine.py
grep -n "litellm.completion\|_litellm.completion" specmetrics/kernel/litellm_engine.py

# Check: no litellm.completion() calls outside gateway in plugins/semantic/llm_provider.py
grep -n "litellm.completion" specmetrics/plugins/semantic/llm_provider.py

# Expected: Only gateway module should call litellm.completion() directly.
# Both extraction files should delegate to gateway.
```

### Scenario 2: Rate Limiting at 5 RPM

**Purpose**: Verify rate limiter enforces configured RPM.

```bash
# Run with 5 RPM limit on a project with multiple documents
specmetrics measure /path/to/project --llm-rpm-limit 5 --verbose

# Expected output during extraction:
#   llm_call | rate_limit_delay=12.0s
#   llm_call | rate_limit_delay=0.0s
#   ...
# Total duration for 10 calls should be at least 120 seconds (2 minutes)

# Verify no provider rate limit errors in output
```

### Scenario 3: Rate Limit Disabled (Backward Compatible)

```bash
# Run with rate limit disabled
specmetrics measure /path/to/project --llm-rpm-limit 0 --verbose

# Expected: No rate_limit_delay messages in logs.
# All LLM calls proceed without artificial delays.
```

### Scenario 4: Batch Reduces Call Count

**Purpose**: Verify batching produces fewer LLM calls than documents.

```bash
# Run on a project with 5 documents, capture structured log
specmetrics measure /path/to/project --llm-rpm-limit 15 2>&1 | grep llm_call | wc -l

# Expected: Number of llm_call events < 5 (fewer calls than documents)
```

### Scenario 5: JSON Mode Eliminates Preprocessing

**Purpose**: Verify all extraction responses parse without markdown stripping.

```bash
# Enable debug logging and capture extraction responses
specmetrics measure /path/to/project --verbose 2>&1 | grep -i "strip_code_fence\|markdown"

# Expected: No output (no markdown stripping needed).
# If grep returns nothing, JSON mode is working.
```

### Scenario 6: Batch Response Parsing

**Purpose**: Verify batched response with JSON keyed by document ID parses correctly.

```bash
python3 -c "
# After running measure with LLM extraction, verify the extraction result:
# - Each document's elements are attributed to the correct document ID
# - No cross-document element leakage
# - All documents in the batch appear in the response

# This is verified via the extraction stage output (csm.json / cfm.json)
# rather than raw LLM response inspection
"
```

### Scenario 7: Environment Variable Configuration

```bash
# Set rate limit via environment variable
export SPECMETRICS_LLM_RPM_LIMIT=8
specmetrics measure /path/to/project --verbose 2>&1 | grep rate_limit_delay

# Expected: Delays enforce 8 RPM pacing

# Override with CLI parameter (takes priority)
specmetrics measure /path/to/project --llm-rpm-limit 3 --verbose 2>&1 | grep rate_limit_delay

# Expected: Delays enforce 3 RPM pacing (CLI overrides env var)
```

### Scenario 8: Fallback to Deterministic on LLM Failure

```bash
# Run with an invalid API key to trigger fallback
SPECMETRICS_LLM_API_KEY=invalid_key specmetrics measure /path/to/project --verbose 2>&1

# Expected: LLM call fails after retries, system falls back to deterministic extraction.
# Output should include: llm_call | status=fallback
# Measurement still completes (using deterministic results).
```

### Scenario 9: Ctrl+C During Rate-Limited Wait

```bash
# Run with low RPM limit to create long wait
specmetrics measure /path/to/large-project --llm-rpm-limit 1 &
PID=$!
sleep 5
kill -INT $PID

# Expected: Clean shutdown with message like:
#   "LLM pipeline interrupted. Completed 2 calls, 8 remaining."
```

## Known Limitations

- BCP SDK calls are NOT rate-limited by the gateway (external SDK manages its own calls)
- Rate limiting is per-process; concurrent `specmetrics measure` invocations in separate terminals do NOT share a rate limiter
- Non-OpenAI providers (Claude, Gemini) may not support native JSON mode; the gateway falls back to prompt-based JSON instructions
- Token counting for batch sizing uses character-based estimates (4 chars ≈ 1 token), not exact tokenization
- The `LiteLLMSemanticEngine` batch path yields the same elements-per-document as individual calls, but element `id` formats differ between the two extraction systems (pre-existing difference, not introduced by this feature)
