# Tasks: OpenTelemetry Publisher

**Input**: Design documents from `/specs/012-opentelemetry-publisher/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/publisher-plugin.md

**Tests**: Not explicitly requested in spec — test tasks included for core scenarios only.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/kernel/`, `specmetrics/plugins/`, `specmetrics/tests/` at repository root
- Paths follow the project structure defined in plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency setup

- [x] T001 Create publisher plugin directory structure at `specmetrics/plugins/publisher/__init__.py`
- [x] T002 Add OpenTelemetry SDK and OTLP exporter dependencies to project configuration
- [x] T003 [P] Create test directory structure at `specmetrics/tests/unit/publisher/` and `specmetrics/tests/integration/mocks/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models and infrastructure that MUST be complete before user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Add `TelemetryPublished` event to `specmetrics/kernel/events.py` (consumed by pipeline; produced by publisher)
- [x] T005 [P] Create `PublisherConfiguration` Pydantic model with all config fields and validation in `specmetrics/plugins/publisher/base.py`
- [x] T006 [P] Create `TelemetryMetric` Pydantic model with metric fields and evidence refs in `specmetrics/plugins/publisher/models.py`
- [x] T007 Create `EvidenceRef` data class for traceability in `specmetrics/plugins/publisher/models.py`
- [x] T008 Create `PublisherStatus` Pydantic model with runtime state fields in `specmetrics/plugins/publisher/base.py`

**Checkpoint**: Foundation ready — models exist, events defined

---

## Phase 3: User Story 2 — Configure telemetry destination and authentication (Priority: P1) 🎯 MVP

**Goal**: Users can configure OTLP endpoints, protocol, authentication, TLS, and timeouts via YAML configuration file. Configuration is validated at startup.

**Independent Test**: Configure a mock OTLP receiver endpoint in YAML, run the pipeline, and verify the publisher connects using the specified protocol and credentials.

### Implementation for User Story 2

- [x] T009 [P] [US2] Implement YAML configuration loader for publisher endpoints in `specmetrics/plugins/publisher/config.py`
- [x] T010 [P] [US2] Implement configuration validation (all fields, edge cases, env var references) in `specmetrics/plugins/publisher/config.py`
- [x] T011 [US2] Implement OTLP exporter factory (gRPC/HTTP selection, TLS, timeout, auth headers) in `specmetrics/plugins/publisher/exporter.py`
- [x] T012 [US2] Add configuration error reporting — descriptive messages for invalid URLs, missing required fields in `specmetrics/plugins/publisher/config.py`

**Checkpoint**: Configuration loading and validation works independently

---

## Phase 4: User Story 1 — Publish functional measurements as OpenTelemetry metrics (Priority: P1) 🎯 MVP

**Goal**: The publisher plugin receives measurement results, converts them to OpenTelemetry metrics, and publishes them via OTLP to configured endpoints.

**Independent Test**: Run the measurement pipeline with publisher enabled and verify structured metrics appear at the configured telemetry endpoint.

### Implementation for User Story 1

- [x] T013 [P] [US1] Create `PublisherPlugin` class implementing the plugin protocol in `specmetrics/plugins/publisher/otel_publisher.py`
- [x] T014 [P] [US1] Implement metric conversion from Canonical Functional Model to OTLP metrics in `specmetrics/plugins/publisher/otel_publisher.py`
- [x] T015 [P] [US1] Implement resource attributes factory from pipeline run metadata in `specmetrics/plugins/publisher/otel_publisher.py`
- [x] T016 [US1] Implement publisher startup sequence (load config, create exporters, start connection) in `specmetrics/plugins/publisher/otel_publisher.py`
- [x] T017 [US1] Implement `publish()` method — enqueue metrics, call OTLP exporter in `specmetrics/plugins/publisher/otel_publisher.py`
- [x] T018 [US1] Implement publisher shutdown (flush remaining metrics, close connections) in `specmetrics/plugins/publisher/otel_publisher.py`
- [x] T019 [US1] Register publisher plugin in `pyproject.toml` entry points under `specmetrics.plugins.publisher`
- [x] T020 [US1] Wire publisher stage into kernel pipeline after Export Layer in `specmetrics/kernel/events.py`

**Checkpoint**: Core publishing works end-to-end for single endpoint, single-run scenario

---

## Phase 5: User Story 3 — Batch publishing with configurable interval (Priority: P2)

**Goal**: Metrics are delivered in batches with configurable interval and max size. Batch timer, queue bounds, and overflow dropping work correctly.

**Independent Test**: Configure a short batch interval, run with enough metrics to trigger multiple batches, and verify metrics arrive in correctly-sized groups.

### Implementation for User Story 3

- [x] T021 [P] [US3] Implement batch accumulator with configurable interval timer in `specmetrics/plugins/publisher/batcher.py`
- [x] T022 [P] [US3] Implement metric queue with bounded size and oldest-drop behavior in `specmetrics/plugins/publisher/batcher.py`
- [x] T023 [US3] Integrate batcher into publisher plugin in `specmetrics/plugins/publisher/otel_publisher.py`
- [x] T024 [US3] Implement retry with exponential backoff for failed batch exports in `specmetrics/plugins/publisher/retry.py`
- [x] T025 [US3] Implement multi-endpoint support — independent publisher instances in `specmetrics/plugins/publisher/otel_publisher.py`

**Checkpoint**: Batch delivery, queue overflow, retry, and multi-endpoint all functional

---

## Phase 6: User Story 4 — Publisher health and status reporting (Priority: P3)

**Goal**: Users can query publisher status to see connection state, metrics published, errors, and queue depth.

**Independent Test**: After a successful publication, query status and verify correct state. Simulate connectivity failure and verify status reflects disconnection.

### Implementation for User Story 4

- [x] T026 [P] [US4] Implement `PublisherStatus` tracker — connection state transitions, counters in `specmetrics/plugins/publisher/base.py`
- [x] T027 [US4] Implement `get_status()` method on publisher plugin in `specmetrics/plugins/publisher/otel_publisher.py`
- [x] T028 [US4] Add CLI command for publisher status in `specmetrics/cli/export_commands.py`
- [x] T029 [US4] Implement automatic reconnection with status updates — detect connection loss, mark disconnected, resume on recovery in `specmetrics/plugins/publisher/batcher.py`

**Checkpoint**: Publisher status visible and accurate in all states

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T030 [P] Create mock OTLP receiver for integration testing in `specmetrics/tests/integration/mocks/mock_otlp_receiver.py`
- [x] T031 [P] Add unit tests for `PublisherConfiguration` validation in `specmetrics/tests/unit/publisher/test_config.py`
- [x] T032 [P] Add unit tests for metric conversion in `specmetrics/tests/unit/publisher/test_metrics.py`
- [x] T033 [P] Add unit tests for batch accumulator and queue in `specmetrics/tests/unit/publisher/test_batcher.py`
- [x] T034 [P] Add unit tests for retry logic in `specmetrics/tests/unit/publisher/test_retry.py`
- [x] T035 Add integration test for end-to-end publisher pipeline in `specmetrics/tests/integration/test_publisher_e2e.py`
- [x] T036 Run quickstart.md validation scenarios

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US2 — Configuration (Phase 3)**: Depends on Foundational — BLOCKS US1
- **US1 — Core Publishing (Phase 4)**: Depends on Foundational + US2
- **US3 — Batching (Phase 5)**: Depends on US1 (enhances the publisher)
- **US4 — Status (Phase 6)**: Depends on US1 (adds status to publisher)
- **Polish (Phase 7)**: Depends on all desired user stories

### User Story Dependencies

- **User Story 2 (P1)**: Config model — no dependencies on other stories
- **User Story 1 (P1)**: Depends on US2 (needs config to connect), but tasks within US1 (metric conversion, resource attributes) can parallel with US2
- **User Story 3 (P2)**: Depends on US1 (batcher wraps the publisher)
- **User Story 4 (P3)**: Depends on US1 (status is a feature of the publisher)

### Within Each User Story

- Models before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

| Task Group | Tasks | Why Parallel |
|------------|-------|-------------|
| Phase 1 setup | T001, T002, T003 | Different files, no dependencies |
| Phase 2 models | T005, T006 | Independent Pydantic models in separate files |
| US2 config impl | T009, T010 | Config loader and validator in same file — sequential |
| US1 metric work | T013, T014, T015 | Plugin class, metric conversion, resource attrs — different files |
| US3 batching | T021, T022 | Batcher and queue in same module — sequential |
| US4 status | T026, T027 | Status model and plugin integration — sequential |
| Phase 7 tests | T030, T031, T032, T033, T034 | All independent test files |

---

## Parallel Example: US1 + US2 Combined

```bash
# Phase 3/4 — Tasks T009-T015 can be dispatched together:
Task: "T009 — YAML config loader in config.py"
Task: "T010 — Config validation in config.py"
Task: "T013 — PublisherPlugin class in plugin.py"
Task: "T014 — Metric conversion in metrics.py"
Task: "T015 — ResourceAttributes factory in metrics.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 — Both P1)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US2 (Configuration)
4. Complete Phase 4: US1 (Core Publishing)
5. **STOP and VALIDATE**: Run the pipeline with a mock endpoint — verify metrics arrive
6. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US2 + US1 → Core publishing complete → Deploy/Demo (MVP!)
3. Add US3 → Batching with retry → Deploy/Demo
4. Add US4 → Status monitoring → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US2 (Configuration) → US1 (Core Publishing)
   - Developer B: Can start on US3 test infrastructure after US1 is stable
3. US4 can be added by either developer after US1 is stable

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- US2 and US1 are both P1 and form the MVP — they are tightly coupled (US2 enables US1)
- Phase 7 tests are optional but recommended for CI validation
