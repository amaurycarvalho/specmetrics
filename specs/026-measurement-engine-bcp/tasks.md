# Tasks: Measurement Engine Plugin — Business Complexity Points (BCP)

**Input**: Design documents from `specs/026-measurement-engine-bcp/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/plugins/`, `specmetrics/tests/` at repository root
- Paths follow the project structure from `plan.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create package directories for the new plugin

- [X] T001 Create `specmetrics/plugins/measurement/bcp/` package with `__init__.py`
- [X] T002 Create test directories: `tests/unit/`, `tests/contract/`, `tests/integration/` if not already present

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models, story generator, SDK adapter, explainer — MUST complete before any user story

### Models

- [X] T003 [P] Create all measurement models (`BCPMeasurementResult`, `BCPWorkItem`, `GeneratedStory`, `SDKResult`, `MeasurementEvidence`, `ExecutionMetadata`, `MeasurementWarning`) in `specmetrics/plugins/measurement/bcp/models.py`

### Story Generator

- [X] T004 Create story generator in `specmetrics/plugins/measurement/bcp/story_generator.py` — `generate_story(fp, cfm) -> str`: converts a FunctionalProcess into a markdown user story string with title, actor names, operations, business rules, data groups, and relationships resolved from the CFM

### SDK Adapter

- [X] T005 Create SDK adapter in `specmetrics/plugins/measurement/bcp/sdk_adapter.py` — `BcpSdkAdapter` class wrapping `BCPClient` with dual import path (`bcp_calculator` / `src.sdk`), retry with exponential backoff (3 attempts: 1s, 2s, 4s), error translation, provider configuration
- [X] T006 Create explainer in `specmetrics/plugins/measurement/bcp/explainer.py` — per-item evidence_refs assembly, SDK response preservation, component breakdown collection

### Package Wiring

- [X] T007 Wire up `specmetrics/plugins/measurement/bcp/__init__.py` to export `BCPMeasurementResult`, `BCPPlugin`, `create_bcp_measurement_metadata`

**Parallel opportunities**: T003, T004 are independent. T005 depends on understanding the SDK API.

**Checkpoint**: Foundation ready — all models, story generator, SDK adapter, and explainer exist.

---

## Phase 3: User Story 1 — Automatic BCP Measurement (Priority: P1) 🎯 MVP

**Goal**: Software estimator runs `specmetrics measure --method bcp` and receives BCP scores for every Functional Process via the SDK.

**Independent Test**: `pytest tests/unit/test_bcp_integration.py -v -k test_full_measurement_flow`

### Tests for User Story 1

- [X] T008 [P] [US1] Unit test for model construction and serialization in `tests/unit/test_bcp_models.py`
- [X] T009 [P] [US1] Unit test for story generator — each FP generates a correctly formatted markdown string with title, actors, operations, rules, data groups in `tests/unit/test_bcp_story_generator.py`
- [X] T010 [P] [US1] Unit test for SDK adapter — `calculate()` calls BCPClient, returns parsed result, handles retry in `tests/unit/test_bcp_sdk_adapter.py`
- [X] T011 [P] [US1] Unit test for SDK adapter — exponential backoff on transient errors, immediate fail on auth errors in `tests/unit/test_bcp_sdk_adapter.py`
- [X] T012 [P] [US1] Unit test for SDK adapter — missing SDK gracefully returns adapter with error state in `tests/unit/test_bcp_sdk_adapter.py`
- [X] T013 [US1] Integration test — mock SDK, known CFM, full measurement flow produces correct BCPWorkItems and total in `tests/unit/test_bcp_integration.py`

### Implementation for User Story 1

- [X] T014 [US1] Create BCP plugin (`BCPPlugin`, `BCPHandler`, `create_bcp_measurement_metadata`) in `specmetrics/plugins/measurement/bcp/plugin.py` — handler subscribes to `MEASUREMENT_COMPLETED`, reads CFM from context, invokes story_generator + sdk_adapter per FP, packages BCPMeasurementResult
- [X] T015 [US1] Register BCP entry point in `pyproject.toml` under `specmetrics.plugins.measurement`

**Checkpoint**: US1 is fully functional — the pipeline can produce BCP scores via the external SDK.

---

## Phase 4: User Story 2 — Explainable Measurement (Priority: P1)

**Goal**: Reviewer inspects why a work item received a particular BCP score, with full SDK response and component breakdown preserved.

**Independent Test**: `pytest tests/contract/test_bcp_measurement.py -v`

### Tests for User Story 2

- [X] T016 [P] [US2] Unit test for explainer — per-item generated_story, SDK response, component_breakdown, evidence_refs in `tests/unit/test_bcp_integration.py`
- [X] T017 [US2] Contract test for measurement API — verify plugin metadata, handler event type, result schema with SDK breakdown per FR-026 in `tests/contract/test_bcp_measurement.py`

### Implementation for User Story 2

- [X] T018 [US2] Implement explainer detail per FR-026 — generated_story, sdk_response, component_breakdown, evidence_refs preservation in `specmetrics/plugins/measurement/bcp/explainer.py`

**Checkpoint**: US2 is fully functional — every BCP score includes the generated story, raw SDK response, component breakdown, and CFM evidence.

---

## Phase 5: User Story 3 — Provider Configuration (Priority: P2)

**Goal**: Organization configures the SDK to use Claude instead of OpenAI via Rule Packs.

**Independent Test**: `pytest tests/unit/test_bcp_sdk_adapter.py -v -k test_provider_config`

### Tests for User Story 3

- [X] T019 [P] [US3] Unit test for provider configuration — adapter initializes with "openai" and "claude", verifies constructor args in `tests/unit/test_bcp_sdk_adapter.py`
- [X] T020 [P] [US3] Unit test for missing API key validation — missing env var emits warning, adapter returns error state in `tests/unit/test_bcp_sdk_adapter.py`

### Implementation for User Story 3

- [X] T021 [US3] Implement provider selection in adapter — read provider config from Rule Pack or environment, pass to `BCPClient(provider=...)` in `specmetrics/plugins/measurement/bcp/sdk_adapter.py`
- [X] T022 [US3] Implement credential validation — check configured provider's env var before SDK call, emit structured warning if missing in `specmetrics/plugins/measurement/bcp/sdk_adapter.py`

**Checkpoint**: US3 is fully functional — organizations can switch between OpenAI and Claude via configuration.

---

## Phase 6: User Story 4 — Pipeline Integration (Priority: P2)

**Goal**: Plugin auto-discovers, executes, and produces output compatible with the SpecMetrics export layer.

**Independent Test**: `pytest tests/integration/test_bcp_pipeline.py -v`

### Tests for User Story 4

- [X] T023 [US4] Integration test for pipeline — CFM → BCP measurement with mocked SDK, result in `ctx.measurement_result`, plugin auto-discovered in `tests/integration/test_bcp_pipeline.py`

### Implementation for User Story 4

- [X] T024 [US4] Implement OpenTelemetry metrics — SDK execution duration histogram, processed story gauge, SDK request counter, SDK error counter following existing patterns in `specmetrics/plugins/measurement/bcp/plugin.py`

**Checkpoint**: US4 is fully functional — plugin auto-discovers, executes, emits observability metrics, and output is export-compatible.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T025 [P] Run full test suite — verify `pytest tests/unit/test_bcp_*.py tests/contract/test_bcp_measurement.py tests/integration/test_bcp_pipeline.py` all pass
- [X] T026 [P] Run quickstart validation scenarios from `specs/026-measurement-engine-bcp/quickstart.md`
- [X] T027 Code cleanup — remove unused imports, verify `ruff check` passes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — first deliverable (MVP)
- **US2 (Phase 4)**: Depends on Foundational — can start in parallel with US1
- **US3 (Phase 5)**: Depends on Foundational (adapter) — can start in parallel with US1
- **US4 (Phase 6)**: Depends on US1 (entry point + handler needed for pipeline)
- **Polish (Phase 7)**: Depends on all desired user stories

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **US2 (P1)**: Can start after Phase 2 — Independently testable via direct result construction
- **US3 (P2)**: Can start after Phase 2 — Independently testable via adapter injection
- **US4 (P2)**: Depends on US1 (needs handler + entry point registered)

### Parallel Opportunities

- T003 and T004 in Phase 2 can run in parallel
- All test tasks in US1 (T008–T013) can run in parallel
- US1, US2, and US3 can be developed in parallel after Phase 2

---

## Parallel Example: User Story 1

```bash
# Launch all US1 tests together:
pytest tests/unit/test_bcp_models.py tests/unit/test_bcp_story_generator.py tests/unit/test_bcp_sdk_adapter.py tests/unit/test_bcp_integration.py -v &

# While tests run, start plugin implementation:
# (tasks T014, T015)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup — Package directories
2. Complete Phase 2: Foundational — Models, story generator, SDK adapter, explainer
3. Complete Phase 3: User Story 1 — Plugin handler, entry point, all US1 tests
4. **STOP and VALIDATE**: Run `pytest tests/unit/test_bcp_*.py -v`
5. Deploy/demo if ready — provides core BCP measurement via SDK

### Incremental Delivery

1. Setup + Foundational → Adapter infrastructure ready
2. Add US1 → Core BCP measurement via SDK → **MVP!**
3. Add US2 → Explainability with full SDK response → Transparency
4. Add US3 → Multi-provider support → Flexibility
5. Add US4 → Pipeline integration + metrics → Production readiness

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (plugin + pipeline + tests)
   - Developer B: User Story 2 (explainer + contract tests)
   - Developer C: User Story 3 (provider config + credential validation)
3. When US1–US3 complete:
   - Developer A: User Story 4 (integration test + metrics)
   - Developer B: Polish (quickstart validation, cleanup)
