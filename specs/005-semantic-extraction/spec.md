# Feature Specification: Semantic Extraction

**Feature Branch**: `005-semantic-extraction`

**Created**: 2026-07-15

**Status**: Draft

**Input**: User description: "F04"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extract semantic elements from specification documents (Priority: P1)

A developer triggers the measurement pipeline on a repository. The Semantic Extraction stage receives normalized documents from the Specification Adapter layer and extracts structured semantic elements — facts, entities, relationships, and operations — while preserving evidence references to the original source.

**Why this priority**: This is the core transformation pipeline stage. Without extraction, no downstream measurement is possible.

**Independent Test**: Can be fully tested by providing a mock set of normalized Document objects, running the extraction stage, and verifying the output contains the expected semantic elements with correct evidence references.

**Acceptance Scenarios**:

1. **Given** a repository containing one specification document with a use case definition, **When** the extraction stage processes the document, **Then** the output contains at least one extracted functional fact with its originating text reference.
2. **Given** a document with no recognized content patterns, **When** the extraction stage processes it, **Then** the stage completes with an empty extraction result and does not fail the pipeline.
3. **Given** multiple documents from different SDD frameworks, **When** the extraction stage processes them, **Then** each document's content is extracted independently and results are consolidated.

---

### User Story 2 - Extraction preserves evidence provenance (Priority: P1)

An analyst inspects a measurement result and needs to verify its origin. Each extracted semantic element carries a reference to the exact document, section, and text fragment that supports it.

**Why this priority**: Principle V (Evidence First) requires every fact to be traceable. Without evidence provenance, measurements cannot be audited or trusted.

**Independent Test**: Can be tested by extracting from a known document and verifying that every extracted element includes a non-empty source reference with document ID, section identifier, and text excerpt.

**Acceptance Scenarios**:

1. **Given** a document with three distinct sections, **When** extraction completes, **Then** each extracted element references the correct section ID and includes the source text fragment.
2. **Given** a cross-document relationship (e.g., a use case that references a business rule in another document), **When** extraction completes, **Then** the relationship element references both source documents.

---

### User Story 3 - Extraction providers are pluggable (Priority: P2)

A new SDD framework introduces a novel document format requiring specialized extraction logic. Rather than modifying the core, a developer implements an extraction provider plugin and registers it via the F02 plugin system.

**Why this priority**: Principle VIII (Plugin-Oriented) requires extension without modification. Plugins ensure the core stays small and stable.

**Independent Test**: Can be tested by implementing a mock extraction provider as a plugin, registering it through F02, and verifying it is invoked when a document of its declared type is processed.

**Acceptance Scenarios**:

1. **Given** two extraction provider plugins installed for different document types, **When** extraction runs on mixed documents, **Then** each document is processed by the correct provider.
2. **Given** an extraction provider that raises an error, **When** extraction runs, **Then** the provider's error is isolated, a warning is logged, and other providers continue processing.

---

### User Story 4 - Industry-standard extraction strategies work out of the box (Priority: P2)

A user runs extraction immediately after installation without configuring any extraction providers. The system includes built-in providers for common SDD frameworks (OpenSpec, SpecKit) and a generic LLM-assisted semantic extraction provider.

**Why this priority**: Principle XII (Open by Default) and getting users to value quickly.

**Independent Test**: Can be tested by installing the platform, providing a repository with OpenSpec documents, and running extraction without any plugin configuration. The built-in providers should discover and process the documents.

**Acceptance Scenarios**:

1. **Given** a repository with OpenSpec documents, **When** extraction runs with no additional plugins configured, **Then** the built-in OpenSpec provider processes the documents.
2. **Given** a repository with unstructured Markdown documents not matching any built-in SDD framework, **When** extraction runs, **Then** the generic LLM-assisted provider processes them.

---

### Edge Cases

- What happens when a provider returns an empty result for a document? The document is logged with a warning, and extraction proceeds with remaining documents.
- How does the system handle a document with binary or non-text content that was not filtered by the adapter layer? The extraction stage performs a content-type sanity check and skips non-text content with a logged warning.
- What happens when the LLM-assisted provider is unavailable (no API key, network error)? Extraction degrades gracefully — the provider returns a best-effort result with whatever structural parsing is possible, and the failure is logged. The pipeline continues.
- How does extraction handle documents that exceed provider context limits? Documents exceeding the provider's capacity are split into chunks with sequential chunk references in evidence provenance.

## Constitution Check *(mandatory)*

**Engaged Principles**: I (Specification First), III (Semantic Before Structural), IV (LLM-Assisted, Deterministic Results), V (Evidence First), VII (Canonical Representation), VIII (Plugin-Oriented), XIV (Layer Independence)

**Compliance Notes**:
- Specification First (I): Extraction consumes normalized Document objects produced by the Specification Adapter layer — it operates on specifications, never on source code.
- Semantic Before Structural (III): The extraction layer is where semantic understanding of specification content is realized. It transforms document structure into functional meaning.
- LLM-Assisted, Deterministic Results (IV): LLMs MAY assist extraction of facts, entities, and relationships, but the extraction interface and evidence provenance model are deterministic. LLM providers are one implementation option.
- Evidence First (V): Every extracted element MUST preserve its source reference. The evidence reference is a first-class field in the extraction output model.
- Plugin-Oriented (VIII): Extraction providers are F02 plugins with type SEMANTIC. New framework support is added by installing a new semantic provider — never by modifying the core.
- Layer Independence (XIV): The extraction stage consumes only the canonical Document model and produces an extraction result consumed by the Evidence Graph layer. No layer depends on another's internal implementation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The extraction stage MUST accept a list of Document objects (as defined by the Specification Adapter interface) and produce a list of extracted semantic elements.
- **FR-002**: Each extracted semantic element MUST include: a unique identifier, a semantic type (fact, entity, relationship, operation), a confidence score, and an evidence reference.
- **FR-003**: Each evidence reference MUST include: the source document ID, the source section ID (if applicable), and the exact text fragment that supports the extracted element.
- **FR-004**: The extraction stage MUST process documents independently — a failure in one document MUST NOT affect extraction of other documents.
- **FR-005**: Extraction providers MUST be discoverable through the F02 plugin system with plugin type SEMANTIC.
- **FR-006**: The system MUST include a built-in LLM-assisted extraction provider capable of processing general specification documents without framework-specific logic.
- **FR-007**: The extraction stage MUST produce a standard output structure consumable by the Evidence Graph layer (F05), including extracted elements, provider metadata, and processing statistics.
- **FR-008**: Users MUST be able to configure which extraction provider handles which document types through a provider routing configuration.
- **FR-009**: The extraction stage MUST log the provider used for each document, the number of elements extracted, and any errors encountered.
- **FR-010**: Documents that cannot be processed by any registered provider MUST be logged with a warning and skipped — the pipeline MUST NOT fail.

### Key Entities *(include if feature involves data)*

- **ExtractedElement**: A semantic element produced by extraction — represents a fact, entity, relationship, or operation identified in a specification document. Contains an identifier, semantic type, confidence score (0.0–1.0, where 1.0 is certain), and evidence reference(s).
- **EvidenceReference**: A pointer back to the source material that justifies an extracted element. Contains source document ID, section ID, and the exact text fragment.
- **ExtractionProvider**: A plugin that implements the extraction interface for one or more document types. Configured via F02 and routed by document type.
- **ExtractionResult**: The output of the extraction stage — a collection of ExtractedElements along with processing metadata (providers used, documents processed, errors, timing).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A repository with 10 specification documents is fully extracted within 30 seconds (including LLM-assisted processing) — measured from stage start to result emission.
- **SC-002**: Every ExtractedElement in the output has a non-empty evidence reference with document ID, section ID (where applicable), and text fragment.
- **SC-003**: A new extraction provider can be added and made operational by implementing a single plugin factory function and registering it — no core code changes required.
- **SC-004**: Adding or removing an extraction provider does not change the output of other providers processing their own documents.
- **SC-005**: A document with malformed content does not prevent other documents from being extracted — the pipeline continues with a warning logged.

## Assumptions

- LLM-assisted extraction requires an API key configured by the user; the built-in provider documents this requirement at installation.
- The Evidence Graph layer (F05) defines the final schema for extracted elements; this spec defines an initial output structure that F05 may refine.
- Existing F02 plugin discovery mechanism is reused for extraction provider discovery — no new discovery infrastructure is needed.
- The canonical Document model from F03 (Specification Adapter Interface) is stable and available as input.
- Extraction providers are stateless — each invocation receives the full document content and produces independent results.
- Built-in LLM provider supports multiple LLM backends through a configurable gateway, with at least one free/open-source backend configured out of the box.
