# Tasks: Configuration System

**Input**: Design documents from `/specs/014-configuration-system/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in specification — test tasks skipped. Quickstart.md provides manual validation scenarios.

**Organization**: Tasks grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/infrastructure/config/`, `specmetrics/cli/`, `specmetrics/plugins/` at repository root
- Paths shown below follow the plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Add `pydantic-settings` dependency to `pyproject.toml`
- [x] T002 [P] Create `specmetrics/infrastructure/config/` package with `__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Create `SourceLevel` enum with SYSTEM, USER, PROJECT, ENVIRONMENT, CLI levels in `specmetrics/infrastructure/config/sources.py`
- [x] T004 [P] Create `ConfigurationSource` base class with `load()` abstract method in `specmetrics/infrastructure/config/sources.py`
- [x] T005 [P] Implement `FileSource(source_path, format)` reading YAML/JSON via ruamel.yaml in `specmetrics/infrastructure/config/sources.py`
- [x] T006 [P] Implement `EnvironmentSource(prefix)` reading env vars with `SPECMETRICS_` prefix in `specmetrics/infrastructure/config/sources.py`
- [x] T007 [P] Implement `CliSource(args)` parsing CLI key=value pairs in `specmetrics/infrastructure/config/sources.py`
- [x] T008 Create core `ConfigurationSchema` Pydantic model with `PipelineSettings` and `LoggingSettings` in `specmetrics/infrastructure/config/schema.py`
- [x] T009 [P] Create `ConfigProvider` protocol with `get()`, `get_model()`, `dump`, and `warnings` in `specmetrics/infrastructure/config/schema.py`
- [x] T010 Create `SourceProvenance` data class in `specmetrics/infrastructure/config/schema.py`
- [x] T011 Create `ConfigWarning` data class in `specmetrics/infrastructure/config/schema.py`
- [x] T012 Implement `Resolver` class with precedence-based deep merge and circular reference detection in `specmetrics/infrastructure/config/resolver.py`

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 — Centralized configuration loading (Priority: P1) 🎯 MVP

**Goal**: Load all configuration from a hierarchy of sources (system → user → project → env → CLI)

**Independent Test**: Provide a valid `specmetrics.yml`, set `SPECMETRICS_LOGGING_LEVEL=debug`, and verify `specmetrics measure` uses the merged config with env var overriding the file value.

### Implementation for User Story 1

- [x] T013 [US1] Implement `Loader` class with XGD-based file discovery and source merging in `specmetrics/infrastructure/config/loader.py`
- [x] T014 [US1] Implement `ConfigurationSystem` class orchestrating sources → resolver → output in `specmetrics/infrastructure/config/loader.py`
- [x] T015 [US1] Add `--config` CLI option to `specmetrics/cli/app.py` with path validation and env var expansion (FR-012)
- [x] T016 [US1] Wire `ConfigurationSystem.load()` into CLI startup flow in `specmetrics/cli/app.py` (FR-001, FR-004)
- [x] T017 [US1] Add `SPECMETRICS_CONFIG_PATH` environment variable support as alternative to `--config` flag
- [x] T018 [US1] Add logging of discovered config sources at startup in `specmetrics/infrastructure/config/loader.py`

**Checkpoint**: At this point, User Story 1 should be fully functional — platform loads config from files, env vars, and CLI args with correct precedence

---

## Phase 4: User Story 2 — Configuration validation with descriptive errors (Priority: P1)

**Goal**: Validate all settings at startup and report descriptive errors for missing required fields, type mismatches, and out-of-range values

**Independent Test**: Provide a config with a type mismatch (e.g., `pipeline.stage_timeout: "not-a-number"`) and verify startup error includes field path, invalid value, and expected type.

### Implementation for User Story 2

- [x] T019 [US2] Implement `Validator` class wrapping Pydantic model validation with descriptive error formatting in `specmetrics/infrastructure/config/validator.py`
- [x] T020 [US2] Create `ConfigValidationError` with field path, invalid value, and expected type in `specmetrics/infrastructure/config/validator.py`
- [x] T021 [US2] Create `ConfigParseError` with file path, line number, and syntax description in `specmetrics/infrastructure/config/validator.py`
- [x] T022 [US2] Integrate validation into `ConfigurationSystem.load()` — validate after merge, before returning in `specmetrics/infrastructure/config/loader.py`
- [x] T023 [US2] Implement unrecognized key warning (FR-008) — warn but continue with defaults in `specmetrics/infrastructure/config/validator.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work — config loads with validation, bad config produces descriptive errors

---

## Phase 5: User Story 3 — Plugin-specific configuration support (Priority: P2)

**Goal**: Plugins declare their config schema during registration; user configures them under `plugins.{id}` namespace

**Independent Test**: Register a test plugin with `MyPluginConfig(api_key=str, timeout=int=30)`, provide `plugins.my-plugin.api_key` in config file, and verify the plugin receives its validated model at initialization.

### Implementation for User Story 3

- [x] T024 [US3] Create `PluginConfigDeclaration` data class and collection mechanism in `specmetrics/infrastructure/config/plugin.py`
- [x] T025 [US3] Implement `register_plugin_schema(plugin_id, schema_model)` on `ConfigurationSystem` in `specmetrics/infrastructure/config/plugin.py`
- [x] T026 [US3] Wire plugin config schema collection into the existing plugin discovery flow in `specmetrics/infrastructure/config/loader.py`
- [x] T027 [US3] Implement plugin namespace allocation under `plugins.{plugin_id}` in merge logic in `specmetrics/infrastructure/config/loader.py`
- [x] T028 [US3] Add plugin config validation — required field missing → validation error with plugin ID in `specmetrics/infrastructure/config/plugin.py`

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work — plugins declare schemas, users configure them under namespace, validation catches plugin config errors

---

## Phase 6: User Story 4 — Configuration introspection and status (Priority: P3)

**Goal**: Inspect active configuration with source-of-origin tracking and sensitive value masking

**Independent Test**: Set `pipeline.stage_timeout` in config, override with env var, run `specmetrics config dump`, and verify the dump shows `stage_timeout` with source=`SPECMETRICS_PIPELINE_STAGE_TIMEOUT` and level=`environment`.

### Implementation for User Story 4

- [x] T029 [US4] Create `ConfigurationDump` and `DumpEntry` data classes with source-of-origin annotations in `specmetrics/infrastructure/config/introspection.py`
- [x] T030 [US4] Implement `build_dump()` function converting `ResolvedConfiguration` to `ConfigurationDump` in `specmetrics/infrastructure/config/introspection.py`
- [x] T031 [US4] Implement sensitive value masking using Pydantic `SecretStr` — mask in dump output in `specmetrics/infrastructure/config/introspection.py`
- [x] T032 [US4] Create `config dump` CLI subcommand as Typer subcommand group in `specmetrics/cli/app.py`
- [x] T033 [US4] Implement `config dump` output formatter (text table + JSON option) in `specmetrics/cli/app.py`
- [x] T034 [US4] Expose `ConfigProvider.dump` property returning `ConfigurationDump` in `specmetrics/infrastructure/config/schema.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T035 [P] Add `pydantic-settings` environment variable mapping for all core settings (FR-001 hierarchy)
- [x] T036 Run `quickstart.md` validation — execute all 10 validation scenarios and verify expected outcomes
- [x] T037 [P] Code cleanup — consistent error handling, logging with structlog, and docstrings across `specmetrics/infrastructure/config/`
- [x] T038 Verify SC-006 — config loads and validates 50+ settings in under 500ms

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 and US2 are P1 and can proceed sequentially (US2 depends on US1's loader)
  - US3 (P2) depends on US1 (needs loader/merge) but not on US2
  - US4 (P3) depends on US1 (needs resolved config) but not on US2 or US3
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational — No dependencies on other stories
- **User Story 2 (P1)**: Depends on US1 (needs `ConfigurationSystem.load()` to validate) — but US1 can skip validation initially
- **User Story 3 (P2)**: Depends on US1 (needs merge/resolver) — independently testable from US2
- **User Story 4 (P3)**: Depends on US1 (needs `ResolvedConfiguration`) — independently testable from US2/US3

### Within Each User Story

- Core implementation before CLI integration
- Models/schemas before services
- Services before CLI/API wiring
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (T004/T005/T006/T007/T008/T009)
- US3 and US4 can start in parallel once US1 completes (if team capacity allows)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Implement Loader class in specmetrics/infrastructure/config/loader.py"
Task: "Add --config CLI option to specmetrics/cli/app.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently via quickstart scenarios 1-3
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (P1) → Centralized loading works → Deploy/Demo (MVP!)
3. Add User Story 2 (P1) → Validation with descriptive errors → Deploy/Demo
4. Add User Story 3 (P2) → Plugin config support → Deploy/Demo
5. Add User Story 4 (P3) → Introspection and dump → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (loader + CLI)
   - Developer B: User Story 2 (validator) — can start after US1 merge TODO
3. After US1 completes:
   - Developer A: User Story 3 (plugin config)
   - Developer B: User Story 4 (introspection)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Phase 8: Convergence

**Purpose**: Close gaps identified by `/speckit.converge` between the specified intent and the current implementation.

- [x] T039 Wire `Validator.validate()` into `ConfigurationSystem.load()` — validate merged config against `CoreConfig` schema before returning per FR-002 (missing)
- [x] T040 Create test files for all config modules: `tests/unit/config/test_loader.py`, `test_schema.py`, `test_sources.py`, `test_validator.py`, `test_resolver.py`, `test_introspection.py`, `test_plugin.py` and `tests/integration/config/test_integration.py` per plan.md (missing)
- [x] T041 Implement `SPECMETRICS_CONFIG_PATH` environment variable support in `ConfigurationSystem.__init__()` per T017 (missing)
- [x] T042 Wire `register_plugin_schema()` into the plugin discovery flow in `PipelineOrchestrator.discover_plugins()` per FR-005 (partial)
- [x] T043 Add `SecretStr` type to sensitive config fields (e.g., API keys) and fix `_mask_if_sensitive()` dead code branch per FR-007 (partial)
