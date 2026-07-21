# Tasks: LLM Batch Processing & Rate Limiting

**Input**: Design documents from `specs/037-llm-batch-rate-limit/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md

**Organization**: Tasks grouped by user story from spec.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core gateway infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No batch integration, rate limiting config, or extraction migration can begin until this phase is complete

- [X] T001 [P] Create `LLMGatewayConfig` extending `LLMProviderConfig` with `rpm_limit`, `max_tokens`, `max_retries`, `batch_max_chars` fields in `specmetrics/kernel/llm_gateway.py`
- [X] T002 [P] Create `RateLimiter` class with sliding-window deque algorithm and `acquire()`/`wait_and_record()` methods in `specmetrics/kernel/llm_gateway.py`
- [X] T003 [P] Create `LLMCallRecord` dataclass with call_id, provider, model, token counts, duration, rate_limit_delay, retry_count, status in `specmetrics/kernel/llm_gateway.py`
- [X] T004 [P] Create `BatchRequest` and `DocumentPayload` models with document_id, content, document_type fields and prompt assembly logic in `specmetrics/kernel/llm_gateway.py`
- [X] T005 [P] Create batch response parser that accepts JSON object keyed by document ID and returns `dict[str, ExtractionResult]` in `specmetrics/kernel/llm_gateway.py`
- [X] T006 Create `LLMGateway` class with `__init__` accepting `LLMGatewayConfig`, `complete()` method (single call), and `complete_batch()` method (batched call) in `specmetrics/kernel/llm_gateway.py`
- [X] T007 Implement `complete()` method in LLMGateway: apply rate limiter, call `litellm.completion()` with `response_format`, parse response, log `LLMCallRecord`, retry on failure (max 3) in `specmetrics/kernel/llm_gateway.py`
- [X] T008 Implement `complete_batch()` method in LLMGateway: assemble batch prompt (document IDs as keys), call `complete()`, parse response, attribute elements per document, handle partial failures in `specmetrics/kernel/llm_gateway.py`

**Checkpoint**: Gateway core ready — extraction systems can now be migrated

---

## Phase 2: User Story 1 - Batch Document Extraction (Priority: P1) 🎯 MVP

**Goal**: Multiple specification documents are grouped into a single LLM call, reducing total call count by 50%+.

**Independent Test**: Run `specmetrics measure` on a project with 5 specification documents. Verify `llm_call` log events count < 5. Verify extracted elements are correctly attributed to source documents.

- [X] T009 [US1] Integrate `LLMGateway` into `ExtractionStage.handle()` — inject gateway from context metadata into providers in `specmetrics/kernel/extraction_stage.py`
- [X] T010 [US1] Update `LiteLLMSemanticEngine` to accept and use `LLMGateway` instead of calling `_litellm.completion()` directly — replace `_call_llm()` body with gateway delegate in `specmetrics/kernel/litellm_engine.py`
- [X] T011 [US1] Update `LLMExtractionProvider.extract()` to accept and use `LLMGateway` instead of calling `litellm.completion()` directly — replace chunk loop with batch call in `specmetrics/plugins/semantic/llm_provider.py`
- [X] T012 [US1] Implement batch size splitting in gateway: when `batch_max_chars` exceeded, split BatchRequest into sub-batches automatically in `specmetrics/kernel/llm_gateway.py`
- [X] T013 [US1] Implement partial batch failure handling: if some document IDs missing from JSON response, retry only those documents individually in `specmetrics/kernel/llm_gateway.py`

**Checkpoint**: Batching functional — fewer LLM calls than documents per run

---

## Phase 3: User Story 2 - Rate Limiting with Configurable RPM (Priority: P1)

**Goal**: Configurable rate limit with rolling-window enforcement, default 15 RPM, settable via CLI, env var, and config file.

**Independent Test**: Configure 5 RPM, run on a project needing 20 calls, verify no provider errors and total time ≥ 4 minutes.

- [X] T014 [US2] Add `--llm-rpm-limit` CLI parameter to `measure` command in `specmetrics/cli/app.py` (int, default 15, 0 = unlimited)
- [X] T015 [US2] Pass `rpm_limit` from CLI through `PipelineRequest` to orchestrator in `specmetrics/cli/measure.py`
- [X] T016 [US2] Read `SPECMETRICS_LLM_RPM_LIMIT` environment variable as fallback config in `LLMGatewayConfig` constructor in `specmetrics/kernel/llm_gateway.py`
- [X] T017 [US2] Wire `rpm_limit` from `PipelineRequest` or config into `LLMGateway` instantiation during pipeline setup in `specmetrics/application/orchestrator.py`
- [X] T018 [US2] Implement rate limiter `wait_and_record()` — compute delay, sleep if needed, record timestamp — in `specmetrics/kernel/llm_gateway.py`
- [X] T019 [US2] Handle `rpm_limit=0` as unlimited (skip rate limiter entirely) in `specmetrics/kernel/llm_gateway.py`
- [X] T020 [US2] Handle Ctrl+C during rate-limited wait: catch KeyboardInterrupt, report completed/remaining counts, exit cleanly in `specmetrics/kernel/llm_gateway.py`

**Checkpoint**: Rate limiting active — all LLM calls paced within configured RPM

---

## Phase 4: User Story 3 - JSON Structured Output Everywhere (Priority: P2)

**Goal**: All extraction LLM calls use `response_format={"type": "json_object"}`, eliminating markdown stripping and regex response cleaning.

**Independent Test**: Run measure with LLM extraction, verify no `_strip_code_fence()` calls and responses parse directly as JSON.

- [X] T021 [US3] Configure gateway to pass `response_format={"type": "json_object"}` to all `litellm.completion()` calls for OpenAI-compatible providers in `specmetrics/kernel/llm_gateway.py`
- [X] T022 [US3] Implement provider detection in gateway (prefix-based: `gpt-` → OpenAI, `claude-` → Anthropic, `gemini-` → Google) for conditional JSON mode in `specmetrics/kernel/llm_gateway.py`
- [X] T023 [US3] Implement JSON mode fallback: for non-OpenAI providers, append "Respond with valid JSON only. No markdown fences." to system prompt in `specmetrics/kernel/llm_gateway.py`
- [X] T024 [US3] Remove `_strip_code_fence()` calls and regex-based response cleaning from `LLMExtractionProvider._parse_response()` in `specmetrics/plugins/semantic/llm_provider.py`
- [X] T025 [US3] Handle JSON parse failure in gateway: retry once with corrected prompt, if still failing log raw response and fall back to deterministic extraction in `specmetrics/kernel/llm_gateway.py`

**Checkpoint**: JSON mode universal — zero response preprocessing needed

---

## Phase 5: User Story 4 - Unified LLM Gateway (Priority: P2)

**Goal**: Both extraction systems route through a single gateway instance; no direct `litellm.completion()` calls remain in extraction code.

**Independent Test**: grep for `litellm.completion` in `specmetrics/kernel/litellm_engine.py` and `specmetrics/plugins/semantic/llm_provider.py` — expected zero matches.

- [X] T026 [US4] Verify `LiteLLMSemanticEngine` no longer calls `litellm.completion()` or `_litellm.completion()` directly — all calls through gateway in `specmetrics/kernel/litellm_engine.py`
- [X] T027 [US4] Verify `LLMExtractionProvider` no longer calls `litellm.completion()` directly — all calls through gateway in `specmetrics/plugins/semantic/llm_provider.py`
- [X] T028 [US4] Instantiate single `LLMGateway` instance at pipeline initialization, inject into both extraction systems via `ExtractionStage` in `specmetrics/kernel/extraction_stage.py`
- [X] T029 [US4] Update `SemanticEngineFactory` to accept optional `LLMGateway` parameter and pass it to engine constructors in `specmetrics/kernel/semantic_extraction_engine.py`
- [X] T030 [US4] Ensure BCP `BcpSdkAdapter` and CLI `llm test` command still call `litellm.completion()` independently — they are excluded from gateway scope in `specmetrics/plugins/measurement/bcp/sdk_adapter.py` and `specmetrics/cli/config_commands.py` (verification only, no code changes needed)
- [X] T031 [US4] Add LLM call summary stats (total calls, total tokens, total duration) to `PipelineResult` from gateway `call_records` in `specmetrics/application/orchestrator.py`

**Checkpoint**: Single gateway instance — consistent rate limiting, JSON mode, and retries across both extraction systems

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Tests, validation, and final verification

- [X] T032 [P] Create unit tests for `RateLimiter`: verify delay computation at limit, no delay below limit, unlimited mode, thread safety in `tests/test_llm_gateway.py`
- [X] T033 [P] Create unit tests for `BatchRequest` prompt assembly and response parsing: valid JSON keyed by doc ID, missing document handling, invalid JSON handling in `tests/test_llm_gateway.py`
- [X] T034 [P] Create unit tests for `LLMGateway.complete()`: rate limit applied, JSON mode passed, retry on failure, fallback behavior in `tests/test_llm_gateway.py`
- [X] T035 [P] Create integration test: run `specmetrics measure` with mock LLM, verify call count < document count (batching) in `tests/test_llm_gateway.py`
- [X] T036 [P] Create integration test: run with `--llm-rpm-limit 5`, verify 20 calls take ≥ 240s in `tests/test_llm_gateway.py`
- [X] T037 [P] Create integration test: verify `SPECMETRICS_LLM_RPM_LIMIT` env var overrides default in `tests/test_llm_gateway.py`
- [X] T038 Run quickstart.md validation scenarios 1-9 and confirm all pass
- [X] T039 Run `ruff check` and `ruff format` on all changed files

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — can start immediately
- **US1 Batch (Phase 2)**: Depends on Phase 1 (gateway core) — BLOCKS MVP
- **US2 Rate Limit (Phase 3)**: Depends on Phase 1 (rate limiter class). Independent from US1 — can run in parallel with Phase 2
- **US3 JSON Mode (Phase 4)**: Depends on Phase 1 (gateway `complete()` method) + Phase 2 (extraction systems use gateway)
- **US4 Unified (Phase 5)**: Depends on Phase 2 + Phase 3 (both systems migrated) — verification and consolidation phase
- **Polish (Phase 6)**: Depends on all user story phases

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational only. No dependencies on other stories.
- **US2 (P1)**: Depends on Foundational only. Can run in parallel with US1.
- **US3 (P2)**: Depends on US1 (needs gateway wired to extraction systems before enforcing JSON mode).
- **US4 (P2)**: Depends on US1 + US2 (verifies both systems migrated and rate limiter shared).

### Within Each Phase

- Phase 1: T001-T005 (5 models) can run in parallel; T006 depends on T001; T007-T008 depend on T002+T004+T006
- Phase 2: T009-T011 can run in parallel (different files); T012-T013 depend on gateway batch method
- Phase 3: T014-T016 can run in parallel; T017-T020 depend on gateway construction
- Phase 4: T021-T023 can run in parallel; T024 depends on T021; T025 depends on T021+T024
- Phase 5: T026-T030 are verification tasks (can run in any order); T031 depends on gateway being wired
- Phase 6: T032-T037 (all tests) can run in parallel; T038-T039 run sequentially after

### Parallel Opportunities

- Phase 1: T001-T005 (5 models in parallel)
- Phase 2: T009 + T010 + T011 (3 extraction integrations in parallel)
- Phase 3: T014 + T015 + T016 (CLI + config + env var in parallel)
- Phase 6: T032-T037 (6 test tasks in parallel)
- **US1 and US2 phases can run in parallel** by different developers (separate concerns, both depend only on Phase 1)

---

## Parallel Example: Foundational Models (Phase 1)

```bash
# All 5 models touch different concerns — launch together:
Task: "Create LLMGatewayConfig in specmetrics/kernel/llm_gateway.py"
Task: "Create RateLimiter class in specmetrics/kernel/llm_gateway.py"
Task: "Create LLMCallRecord dataclass in specmetrics/kernel/llm_gateway.py"
Task: "Create BatchRequest + DocumentPayload models in specmetrics/kernel/llm_gateway.py"
Task: "Create batch response parser in specmetrics/kernel/llm_gateway.py"
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Foundational (gateway core)
2. Complete Phase 2: US1 (batch extraction)
3. **STOP and VALIDATE**: Run `specmetrics measure` on a multi-document project, verify call count < document count
4. Quick delivery: batching alone cuts costs by 50%+

### Incremental Delivery

1. Foundational → Gateway core ready
2. Add US1 → Batch extraction working (MVP!)
3. Add US2 → Rate limiting active (production-ready)
4. Add US3 → JSON mode eliminates fragile parsing
5. Add US4 → Consolidation verified
6. Polish → Tests and validation complete

### Parallel Team Strategy

With multiple developers:
1. Team completes Phase 1 together (gateway core)
2. Once Foundational is done:
   - Developer A: US1 (batch extraction, Phase 2)
   - Developer B: US2 (rate limiting, Phase 3) — in parallel with A
3. After US1+US2 complete:
   - Developer A: US3 (JSON mode, Phase 4)
   - Developer B: US4 (unified gateway verification, Phase 5)
4. Both: Polish (Phase 6)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- T026 and T027 are verification-only tasks for US4 (confirm grep returns zero); no code changes expected if T010/T011 are done correctly
- T030 is also verification-only — confirms BCP and CLI test are NOT modified
- The `LLMGateway` file (`kernel/llm_gateway.py`) accumulates many Phase 1 tasks (T001-T008) — they should be implemented in dependency order since they're in the same file
- Rate limiting is per-process; integration tests should use mock LLM to avoid actual API calls
- The gateway should NOT modify `PipelineContext` structure — it's injected at pipeline setup and stored on the orchestrator or extraction stage

---

## Phase 7: Convergence

**Purpose**: Close gaps identified by `/speckit.converge` after initial implementation.

- [X] T040 Create `tests/test_llm_gateway.py` with unit tests for RateLimiter (delay/no-delay/unlimited), BatchRequest (prompt assembly, split, response parsing), and LLMGateway.complete() (retry, fallback) per T032-T037 (missing)
- [X] T041 Add explicit response format instruction to `BatchRequest.assemble_prompt()` — append `Respond with a JSON object keyed by document ID: {"<doc_id>": {"elements": [...]}}` per FR-004, plan: Design Decision 2 (partial)
- [X] T042 Integrate config file fallback for `rpm_limit` into `LLMGatewayConfig` constructor by reading from `_load_llm_config()` or similar config source per FR-011 (partial)
- [X] T043 Add missing-document detection in `parse_batch_response()` by tracking which document IDs from `batch.documents` appear in the JSON response; trigger individual retry for absent docs in `complete_batch()` per US1/AC4 (partial)
