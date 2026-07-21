# Feature Specification: LLM Batch Processing & Rate Limiting

**Feature Branch**: `037-llm-batch-rate-limit`

**Created**: 2026-07-21

**Status**: Draft

**Input**: User description: "Identifique como o specmetrics usa o litellm para analisar as especificações do speckit e do openspec. Analise o cenário onde a LLM é usada e proponha como otimizar o uso de tokens pelo specmetrics na integração com o litellm. O objetivo é fazer o mínimo de hits por minuto no provedor LLM (buscar um máximo de 15 hits por minuto), fazendo o envio em lote das informações necessárias e solicitando respostas da LLM em formato json de forma que o specmetrics consiga extrair mais fácil o resultado e com menos quantidade de hits."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Batch Document Extraction (Priority: P1)

As a platform user running `specmetrics measure` on a project with multiple specification documents, I want the semantic extraction to group multiple documents into a single LLM call rather than making one call per document or per chunk. This reduces the total number of LLM calls, lowering costs and keeping within the provider's rate limits (target: maximum 15 calls per minute).

**Why this priority**: This is the primary mechanism to reduce hit count. Currently, extraction makes 1 call per document chunk — a 10-document project with 3 chunks each produces 30 calls. Batching can reduce this to 2-3 calls, an order-of-magnitude improvement.

**Independent Test**: Run `specmetrics measure` on a project with 5 specification documents. Verify that the total LLM calls made during extraction is less than the number of documents (calls < 5), confirming batching is in effect. Verify that the extracted semantic elements are identical to what would have been extracted with per-document calls.

**Acceptance Scenarios**:

1. **Given** a project with 5 specification documents totaling 30,000 characters, **When** the user runs `specmetrics measure`, **Then** the extraction stage makes at most 3 LLM calls (instead of 5+ individual calls), and all documents' semantic elements are correctly extracted and attributed to their source documents.

2. **Given** a project with a single large document (20,000 characters), **When** the user runs `specmetrics measure`, **Then** the document is split into the minimum number of batch-sized chunks (e.g., 2 calls instead of potentially 4+ at default 8K chunk size).

3. **Given** a batch extraction call that fails, **When** the system retries, **Then** it retries only that specific batch, not all documents, and the retry count is bounded by the configured maximum.

4. **Given** a partial batch failure where some documents in the batch produce errors, **When** the LLM response contains valid data for some but not all documents, **Then** successfully extracted elements are preserved; only the failed documents are retried individually.

---

### User Story 2 - Rate Limiting with Configurable RPM (Priority: P1)

As a platform user with a limited LLM provider quota (e.g., 15 requests per minute), I want SpecMetrics to automatically throttle LLM calls to stay within the configured rate limit, queuing requests when the limit would be exceeded. This prevents provider rate-limit errors and avoids unnecessary retries.

**Why this priority**: Without rate limiting, rapid sequential calls can exceed provider quotas, causing errors, retries, and wasted tokens. A rate limiter with configurable RPM is the foundation for reliable LLM usage under constrained quotas.

**Independent Test**: Configure the rate limit to 5 RPM, run `specmetrics measure` on a project that would normally trigger 20 LLM calls, and measure wall-clock time. Verify no provider rate-limit errors occur and the total duration reflects the throttled rate (at least 4 minutes for 20 calls at 5 RPM).

**Acceptance Scenarios**:

1. **Given** the rate limit is configured to 10 RPM, **When** the extraction stage needs to make 20 LLM calls for a project, **Then** calls are spaced such that no more than 10 occur in any 60-second window, and no provider rate-limit errors are raised.

2. **Given** the rate limit is configured to 15 RPM and a run needs only 5 calls, **When** the user runs `specmetrics measure`, **Then** no artificial delays are introduced — calls proceed as fast as the provider responds.

3. **Given** a configuration where the rate limit is set to 0 or disabled, **When** the user runs `specmetrics measure`, **Then** the system behaves as before (no throttling), preserving backward compatibility.

4. **Given** the rate limiter is active and a call is queued, **When** the user interrupts the process (Ctrl+C), **Then** the system cleanly shuts down and reports how many calls were completed and how many remain.

---

### User Story 3 - JSON Structured Output Everywhere (Priority: P2)

As a developer maintaining SpecMetrics, I want all LLM calls to request structured JSON output using the provider's native JSON mode (`response_format`), so that responses are guaranteed to be valid JSON and do not require fragile markdown-stripping or regex-based parsing.

**Why this priority**: Structured JSON mode eliminates parsing ambiguity, reduces response tokens (no explanatory text), and simplifies the extraction pipeline. It's a prerequisite for reliable batch processing where a single malformed response could affect multiple documents.

**Independent Test**: Run `specmetrics measure` with LLM extraction enabled. Verify that every LLM call includes `response_format={"type": "json_object"}` (or the provider's equivalent). Verify that no `_strip_code_fence()` or regex-based response cleaning is required for any extraction call.

**Acceptance Scenarios**:

1. **Given** an LLM extraction call with JSON mode enabled, **When** the provider returns a response, **Then** the response body is valid JSON that can be parsed with `json.loads()` without any preprocessing (no markdown fence stripping, no regex cleanup).

2. **Given** JSON mode is requested but the provider returns invalid JSON (edge case), **When** the system detects a parse error, **Then** it retries the call with a corrected prompt, and if still failing, logs the raw response for debugging before falling back to deterministic extraction.

3. **Given** all extraction calls use JSON mode, **When** comparing token usage before and after, **Then** the average response token count decreases (because the LLM no longer emits explanatory prose alongside the JSON).

---

### User Story 4 - Unified LLM Gateway (Priority: P2)

As a developer maintaining SpecMetrics, I want a single, unified LLM gateway abstraction that handles all extraction LLM calls with consistent JSON mode, rate limiting, retry logic, and error handling. This eliminates the current duplication where two separate extraction systems (`LiteLLMSemanticEngine` and `LLMExtractionProvider`) each implement their own LLM interaction logic.

**Why this priority**: The current codebase has three separate LLM call implementations with different retry strategies, different response parsing, and no shared rate limiting. A unified gateway reduces code duplication, ensures consistent behavior, and makes future LLM-based features easier to add.

**Independent Test**: Verify that both extraction systems (`LiteLLMSemanticEngine` and `LLMExtractionProvider`) delegate LLM calls to a single gateway class rather than calling `litellm.completion()` directly.

**Acceptance Scenarios**:

1. **Given** the unified gateway is active, **When** any component needs to call an LLM, **Then** it calls a single gateway method that applies rate limiting, JSON mode, retry logic, and error handling consistently.

2. **Given** the gateway is configured with a rate limit of 15 RPM, **When** the two extraction providers (`LiteLLMSemanticEngine` and `LLMExtractionProvider`) both make calls through the gateway, **Then** they share the same rate limiter instance and together stay within the 15 RPM budget.

3. **Given** a new LLM-based feature is added in the future, **When** the developer integrates it, **Then** they only need to construct a prompt and call the gateway — rate limiting, JSON mode, and retries are inherited automatically.

---

### Edge Cases

- What happens when a batch exceeds the provider's maximum context window?
  - The gateway splits the batch into smaller sub-batches that fit within the configured max tokens, transparently to the caller.

- What happens when the rate limiter queue grows very large (e.g., 100+ queued calls)?
  - The system logs a warning with the queue depth and estimated completion time. Processing continues without data loss.

- What happens when a batched call times out?
  - The gateway retries the batch with exponential backoff. After max retries, individual documents from the failed batch are retried one at a time.

- What happens during concurrent pipeline runs (multiple terminal sessions)?
  - Rate limiting is per-process. Each process independently manages its own rate limiter. Cross-process coordination is out of scope.

- What happens when JSON mode is not supported by the configured provider?
  - The gateway falls back to prompt-based JSON instructions (append "Respond with JSON only" to the system prompt) and applies response cleaning as a last resort. A warning is logged.

## Constitution Check *(mandatory)*

**Engaged Principles**:

- **IV - LLM-Assisted, Deterministic Results**: LLMs assist extraction but do not perform measurement. This feature optimizes the LLM integration layer, preserving the boundary between LLM-assisted extraction and deterministic measurement.
- **VIII - Plugin-Oriented Architecture**: The unified gateway is a kernel-level service that plugins consume, consistent with the pattern where the kernel coordinates plugins.
- **X - AI-Friendly by Design**: Optimized LLM usage with lower costs and reliable rate limiting makes the platform more practical for AI-assisted workflows.
- **XIII - Evolution Without Disruption**: Batching and rate limiting are additive optimizations. They do not change the semantic output format or invalidate previously generated measurements.
- **XIV - Layer Independence**: The gateway abstraction sits at the kernel/infrastructure boundary, exposing a stable interface to extraction and measurement plugins without coupling them to specific provider implementations.

**Compliance Notes**: The feature does not change what the LLM extracts — same prompts, same expected output structure. It changes only how calls are grouped (batching), paced (rate limiting), and what response format is requested (JSON mode). Deterministic measurement engines are unaffected.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a configurable rate limit for LLM calls, expressed in requests per minute (RPM), defaulting to 15 RPM.
- **FR-002**: The system MUST enforce the rate limit by delaying calls when the configured RPM would be exceeded within a rolling 60-second window.
- **FR-003**: The system MUST support disabling rate limiting (value 0 or "unlimited") to preserve backward compatibility for users without provider quotas.
- **FR-004**: The extraction stage MUST batch multiple specification documents into a single LLM call, up to a configurable maximum batch size (in tokens or characters), reducing total call count. The batched prompt MUST instruct the LLM to return results as a JSON object keyed by document ID (e.g., `{"doc-1": {"elements": [...]}, "doc-2": {"elements": [...]}}`), so each document's semantic elements are unambiguously attributed.
- **FR-005**: When a batch exceeds the provider's maximum context window, the system MUST automatically split it into sub-batches that fit, with no data loss.
- **FR-006**: All LLM calls in the extraction pipeline MUST request structured JSON output using the provider's native JSON mode (`response_format={"type": "json_object"}` for OpenAI-compatible providers).
- **FR-007**: The system MUST NOT require markdown fence stripping, regex cleaning, or other heuristic response preprocessing when JSON mode is active and the provider responds correctly.
- **FR-008**: The system MUST provide a unified LLM gateway for extraction calls (both `LiteLLMSemanticEngine` and `LLMExtractionProvider`) that applies consistent rate limiting, JSON mode, and retry logic. BCP SDK calls are excluded from the gateway and continue using their existing adapter with independent rate limiting.
- **FR-009**: The gateway MUST implement consistent retry logic with exponential backoff (max 3 retries) for transient failures (rate limits, timeouts, server errors).
- **FR-010**: The gateway MUST preserve the existing fallback behavior: when LLM extraction fails after retries, the system falls back to deterministic semantic extraction.
- **FR-011**: The rate limit configuration MUST be settable via environment variable (`SPECMETRICS_LLM_RPM_LIMIT`), configuration file, and CLI parameter `--llm-rpm-limit`.
- **FR-012**: The system MUST log each LLM call with: provider, model, prompt token count, response token count, duration, and whether rate limiting delayed the call.

### Key Entities

- **LLMGateway**: Centralized abstraction for all LLM interactions. Encapsulates rate limiting, JSON mode, retry logic, and provider-agnostic call execution. Components call `gateway.complete(prompt, system_message, response_schema)` instead of `litellm.completion()` directly.
- **RateLimiter**: Tracks LLM call timestamps in a rolling window. Given a configured RPM limit, determines whether the next call can proceed immediately or must be delayed. Exposes queue depth and estimated wait time.
- **BatchRequest**: Represents a group of documents (or document chunks) to be sent in a single LLM call. Contains the prompt template and a list of document payloads, each tagged with a unique document ID. The gateway assembles the final prompt instructing the LLM to respond with a JSON object keyed by document ID, then parses the response back into per-document results by iterating over the keys.
- **LLMCallRecord**: Log entry for each LLM call with provider, model, token counts (prompt and response), duration, rate-limit delay, retry count, and success/failure status.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a project with 10 specification documents, the extraction stage makes at most 5 LLM calls (50% reduction from the current one-call-per-document approach).
- **SC-002**: When rate limit is configured to 15 RPM and the pipeline needs 30 calls, the total LLM execution time is at least 120 seconds (confirming throttling is active), and zero provider rate-limit errors occur.
- **SC-003**: 100% of extraction LLM calls produce responses that are directly parseable as JSON without preprocessing (no markdown stripping, no regex cleanup required).
- **SC-004**: The unified gateway reduces the number of distinct `litellm.completion()` call sites in the codebase from 3 to 1 — both `LiteLLMSemanticEngine` and `LLMExtractionProvider` route through the gateway, while the CLI test command and BCP SDK adapter remain independent.
- **SC-005**: A new LLM-based feature can be integrated by implementing only a prompt builder and calling the gateway — rate limiting, JSON mode, and retries require zero additional code in the feature module.

## Clarifications

### Session 2026-07-21

- Q: How should the batched LLM prompt instruct the model to format its response for multiple documents? → A: JSON object keyed by document ID — `{"doc-1": {"elements": [...]}, "doc-2": {"elements": [...]}}`. Isolates each document's results, easy to detect missing documents.
- Q: What is the actual scope of BCP integration with the unified gateway? → A: BCP is excluded from the unified gateway scope. The gateway manages extraction calls only. BCP continues using its own SDK adapter with separate rate limiting.

## Assumptions

- The LiteLLM library supports `response_format={"type": "json_object"}` for all OpenAI-compatible providers (GPT-4, GPT-4o, GPT-4o-mini). Non-OpenAI providers (Claude via Anthropic API, Gemini) may require provider-specific JSON mode configuration.
- The existing prompt content and semantic element schema do not need to change — batching only changes how prompts are assembled (multiple documents in one prompt), not what is asked.
- The default rate limit of 15 RPM is a safe baseline for most free-tier and low-tier provider plans. Users with higher quotas can increase it; users without quotas can disable it.
- BCP SDK calls continue using the existing `BcpSdkAdapter` with its own retry logic. The SDK is an external dependency whose internal LLM calls are a black box; gateway integration is not feasible without forking the SDK.
- The `LiteLLMSemanticEngine` (legacy extraction engine) will be updated to use the gateway rather than removed, preserving compatibility for existing configurations.
- Token counting for batch splitting uses conservative estimates based on character count (4 chars ≈ 1 token) rather than exact tokenization, which is sufficient for batch sizing decisions.
