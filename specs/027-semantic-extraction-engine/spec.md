# Feature Specification: Semantic Extraction Engine

**Feature Branch**: `027-semantic-extraction-engine`

**Created**: 2026-07-17

**Status**: Draft

**Input**: User description: "Semantic Extraction Engine"

## Clarifications

### Session 2026-07-17

- **Q1**: When the LiteLLM engine encounters an LLM provider failure, should it fall back to deterministic extraction or fail cleanly? → **A**: Fail cleanly — LiteLLM engine reports the error and produces no extraction output; pipeline continues with empty/error results.
- **Q2**: How should extracted elements be uniquely identified? → **A**: Content-hash IDs — IDs derived from document ID + section path + text content hash, ensuring deterministic identity across runs.
- **Q3**: What priority policy determines which rule applies when multiple rules match the same content? → **A**: Explicit priority scores — each rule has a numeric priority (1–100); higher score wins on conflict. Default priority assigned by rule pack.
- **Q4**: Should the LiteLLM engine produce confidence scores, and if so, how? → **A**: Yes — LLM confidence via logprobs. LiteLLM engine maps model logprobs or token probabilities to the 0.0–1.0 confidence scale, producing model-specific values independent of the deterministic confidence table.
- **Q5**: What minimum set of extraction statistics should the engine report? → **A**: Standard set — documents processed, elements extracted, elements by type, processing duration (ms), errors/warnings count.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run pipeline without LLM configuration (Priority: P1)

A user sets the LLM provider to `none` and runs the measurement pipeline on a repository. The system performs semantic extraction using only deterministic structural analysis — no API keys, network access, or external AI services are required. The pipeline completes successfully and produces the same structured extraction result it would with an LLM.

**Why this priority**: This is the zero-configuration path. Without this story, the pipeline requires an external dependency to function. FR-011 mandates the pipeline works without an LLM.

**Independent Test**: Can be fully tested by configuring `provider = none`, running the pipeline on a repository with known specification documents, and verifying that extraction completes with structured semantic elements and evidence references.

**Acceptance Scenarios**:

1. **Given** a user has configured the LLM provider to `none`, **When** they run the measurement pipeline on a repository with specification documents, **Then** extraction completes successfully without any network access or API key configuration.
2. **Given** the deterministic engine processes a document with headings, lists, tables, code blocks, and blockquotes, **When** extraction completes, **Then** the output contains semantic elements for each recognized structural pattern.
3. **Given** the same document is processed twice with the deterministic engine, **When** both extractions finish, **Then** the outputs are byte-identical.

---

### User Story 2 - Run pipeline with LLM-assisted extraction (Priority: P1)

A user configures an LLM provider (e.g., `chatgpt`, `claude`, `gemini`, or `ollama`) and runs the pipeline. The system selects the LiteLLM-backed extraction engine. Extraction builds upon deterministic analysis and may infer implicit relationships, enrich entities, or classify business concepts. All evidence references from the extraction are preserved.

**Why this priority**: This is the enhanced extraction path. Users who want deeper semantic understanding configure an LLM provider without changing any other pipeline configuration.

**Independent Test**: Can be tested by configuring an LLM provider, running the pipeline on the same documents used for deterministic extraction, and verifying the output uses the same data model and includes all evidence references.

**Acceptance Scenarios**:

1. **Given** a user has configured `chatgpt` as the LLM provider with a valid API key, **When** they run the pipeline, **Then** the LiteLLM-backed extraction engine is selected and extraction completes.
2. **Given** both deterministic and LLM-assisted engines process the same document, **When** both extractions complete, **Then** both outputs conform to the same ExtractionResult data model and every element includes an evidence reference.
3. **Given** a user switches from `none` to `claude`, **When** they run the pipeline, **Then** no downstream pipeline stages require reconfiguration — only the extraction engine changes internally.

---

### User Story 3 - LLM provider becomes unavailable (Priority: P2)

A user has configured an LLM provider, but during pipeline execution the provider is unreachable (network outage, rate limiting, or authentication failure). The engine detects the failure, logs the error with a descriptive message, and reports the failure without corrupting pipeline state or leaving the pipeline in an inconsistent state.

**Why this priority**: FR-012 requires graceful failure. Pipeline state integrity is more important than availability of an optional enhancement.

**Independent Test**: Can be tested by configuring an LLM provider with an invalid API key or simulating a network timeout during extraction, and verifying the pipeline reports the failure and does not enter a corrupted state.

**Acceptance Scenarios**:

1. **Given** an LLM provider is configured but returns authentication errors, **When** the extraction engine attempts to use it, **Then** the engine reports the failure with a descriptive error message and the pipeline state remains valid.
2. **Given** an LLM provider times out during extraction, **When** the engine detects the timeout, **Then** the failure is logged and reported without side effects on subsequent pipeline stages.

---

### User Story 4 - Extend rule-based extraction with custom rules (Priority: P3)

A team wants to recognize a custom specification pattern specific to their domain (e.g., "Safety Constraint" or "Performance Target"). They add a new rule to the rule library without modifying the core engine. The deterministic engine loads and applies the custom rule alongside built-in rules in subsequent extractions.

**Why this priority**: FR-008 requires an extensible rule library. This supports Principle IX (Rule Externalization) — organizational policies remain external to the platform.

**Independent Test**: Can be tested by registering a new rule definition file, processing a document that contains the custom pattern, and verifying the output includes the expected semantic elements for that pattern.

**Acceptance Scenarios**:

1. **Given** a new rule definition for "Safety Constraint" is added to the rule library, **When** the deterministic engine processes a document containing a safety constraint pattern, **Then** the output includes a corresponding semantic element.
2. **Given** a custom rule (priority 80) conflicts with a built-in rule (priority 50) on the same content, **When** the engine loads both rules, **Then** the custom rule wins and its extracted element is produced; the conflict is logged.

---

### Edge Cases

- What happens if a document contains no recognizable structural patterns? The deterministic engine produces an empty extraction result and the pipeline continues with a logged warning.
- How does the system handle documents with extremely deeply nested headings (e.g., 10+ levels)? The engine processes up to a configurable maximum heading depth and flattens beyond it with a logged note.
- What happens if both an LLM provider and the deterministic engine are configured? The LLM provider selection determines the engine — only one engine is active per pipeline run.
- How does the system handle rule definitions with syntax errors? Invalid rules are skipped with a logged warning; the engine loads all valid rules and continues.

## Constitution Check *(mandatory)*

**Engaged Principles**: I (Specification First), III (Semantic Before Structural), IV (LLM-Assisted, Deterministic Results), V (Evidence First), VII (Canonical Representation), VIII (Plugin-Oriented), IX (Rule Externalization), XIV (Layer Independence)

**Compliance Notes**:
- Specification First (I): The engine consumes normalized specification documents produced by the Specification Adapter layer — extraction operates on specifications as the primary source of functional knowledge.
- Semantic Before Structural (III): The engine transforms document structure into canonical semantic elements, prioritizing extraction of functional meaning over document format.
- LLM-Assisted, Deterministic Results (IV): LLMs MAY assist extraction but the engine interface, output model, and evidence provenance are deterministic. The DeterministicSemanticEngine performs all extraction without AI. LiteLLMSemanticEngine uses LLMs only for semantic enrichment, never for measurement.
- Evidence First (V): Every extracted element MUST preserve its source evidence — document ID, section reference, and text fragment. Evidence is a first-class field in the output model.
- Canonical Representation (VII): Both engines produce identical ExtractionResult models. Downstream stages consume only this canonical model and never depend on which engine produced it.
- Plugin-Oriented (VIII): Additional engine implementations MAY be added as plugins without changing the public interface.
- Rule Externalization (IX): Extraction rules (User Story, GWT, Business Rules, etc.) are represented as external rule definitions, not embedded in code. The rule library is extensible.
- Layer Independence (XIV): The engine is selected once during pipeline initialization via SemanticEngineFactory. The pipeline invokes only the SemanticExtractionEngine interface. No downstream component knows the implementation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST expose a single public abstraction `SemanticExtractionEngine` as the extraction interface.
- **FR-002**: The selected engine implementation MUST be resolved from the configured LLM provider during pipeline initialization.
- **FR-003**: When the configured provider is `none`, the system MUST instantiate the `DeterministicSemanticEngine`.
- **FR-004**: When the configured provider is supported by LiteLLM (chatgpt, claude, gemini, ollama), the system MUST instantiate the `LiteLLMSemanticEngine`.
- **FR-005**: The pipeline MUST invoke only the `SemanticExtractionEngine` interface — no downstream component may depend on a specific engine implementation.
- **FR-006**: The `DeterministicSemanticEngine` MUST perform extraction without any external services (no network access, API keys, or AI services).
- **FR-007**: The `DeterministicSemanticEngine` MUST analyze at least: headings, document hierarchy, markdown lists, markdown tables, emphasis, fenced code blocks, blockquotes, and links.
- **FR-008**: The `DeterministicSemanticEngine` MUST support rule-based extraction with an extensible rule library. Built-in rules MUST include at minimum: User Story, Given/When/Then, Requirement statements, Business Rules, Actors, Constraints, Assumptions, Decisions, and Glossary Terms.
- **FR-009**: Both engines MUST produce identical output models (`ExtractionResult`).
- **FR-010**: Both engines MUST preserve evidence references on every extracted semantic element.
- **FR-011**: The pipeline MUST continue operating when no external LLM is configured.
- **FR-012**: If an LLM provider becomes unavailable during extraction, the engine MUST fail cleanly — report the failure with a descriptive message, produce no extraction output, and leave the pipeline state uncorrupted. The engine MUST NOT silently fall back to deterministic extraction.
- **FR-013**: The CLI and MCP APIs MUST expose only LLM provider configuration — the concept of semantic engines MUST remain an internal implementation detail.

### Key Entities *(include if feature involves data)*

- **SemanticExtractionEngine**: The public interface that all extraction engines implement. Defines the contract for transforming documents into semantic elements.
- **ExtractionResult**: The canonical output model produced by both engines. Contains extracted semantic elements, evidence references, and processing metadata including extraction statistics (documents processed, elements extracted, elements by type, processing duration in ms, errors/warnings count).
- **ExtractedElement**: A single semantic fact, entity, relationship, or operation identified during extraction. Includes a deterministic content-hash ID (derived from document ID, section path, and text content), a semantic type, the extracted content, a confidence score (0.0–1.0), and evidence references. Deterministic engine assigns confidence per RFC-031 table; LiteLLM engine derives confidence from model logprobs.
- **EvidenceReference**: A pointer to the original source — document ID, section identifier, and exact text fragment that justifies the extracted element.
- **ExtractionRule**: A definition in the rule library that recognizes a specific specification pattern (e.g., "User Story", "Business Rule"). Rules are external to the engine and have a numeric priority score (1–100) for conflict resolution — higher score wins when multiple rules match the same content.
- **SemanticEngineFactory**: The factory that resolves the configured LLM provider to the correct engine implementation during pipeline initialization.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can configure `provider = none` and run the full measurement pipeline on a repository with 10 specification documents — extraction completes in under 5 seconds without any API key, network access, or external service.
- **SC-002**: Processing the same document set twice with `provider = none` produces byte-identical extraction output across both runs.
- **SC-003**: Switching the configured LLM provider (e.g., from `none` to `chatgpt`) requires no changes to pipeline configuration, downstream stages, or extraction output handling.
- **SC-004**: Every `ExtractionResult` produced by either engine — regardless of provider — contains a non-empty evidence reference (document ID + section + text fragment) on every extracted element.
- **SC-005**: A new extraction rule can be added to the rule library and applied to documents without modifying engine source code or restarting the application.

## Assumptions

- The canonical Document model from the Specification Adapter layer is stable and available as input to the extraction engine.
- The provider-to-engine mapping table (none → DeterministicSemanticEngine, all others → LiteLLMSemanticEngine) covers all required providers at initial release. New providers may require mapping updates.
- LiteLLM is the sole LLM gateway integration for v1; additional gateways may be added in future releases through the same engine interface.
- Rule definitions are stored as external files (e.g., YAML or JSON) and loaded at engine initialization — no runtime rule compilation is required.
- The deterministic engine operates on parsed Markdown AST — a Markdown parser is available and produces a tree structure the engine can traverse.
- Evidence references point to the original document location only — they do not include snapshot or version information.
- The engine factory runs once per pipeline initialization; engine selection is fixed for the duration of a single pipeline execution.

## Backward Compatibility

This feature is fully backward compatible. No CLI, MCP, or plugin changes are required. Existing extraction providers continue to operate unchanged. The `SemanticEngineFactory` and engine interface are additive — they wrap the existing extraction infrastructure without modifying it.

## Future Extensions

Possible future engine implementations that can be added without pipeline changes:

- **CachedSemanticEngine**: Caches extraction results for unchanged documents between runs.
- **MCPSemanticEngine**: Exposes extraction capabilities through the MCP interface directly.
- **HybridSemanticEngine**: Combines deterministic and LLM-assisted extraction within a single engine.
- **RemoteSemanticEngine**: Delegates extraction to a remote service or gRPC endpoint.

New engines are added by extending `SemanticEngineFactory`'s mapping and implementing the `SemanticExtractionEngine` Protocol — no pipeline reconfiguration required.
