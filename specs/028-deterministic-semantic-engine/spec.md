# Feature Specification: Deterministic Semantic Engine

**Feature Branch**: `028-deterministic-semantic-engine`

**Created**: 2026-07-17

**Status**: Draft

**Input**: User description: "Deterministic Semantic Engine"

## Clarifications

### Session 2026-07-17

- **Q1**: How should extracted elements be uniquely identified? → **A**: Reuse F27 content-hash IDs — `sha256(document_id + "::" + section + "::" + text)[:16]`. Same scheme as the LiteLLM engine.
- **Q2**: What priority policy determines which rule wins when multiple rules match the same content? → **A**: Numeric priority scores (1–100). Higher score wins. Ties broken by rule ID lexicographic order.
- **Q3**: What extraction statistics should the engine report? → **A**: Match F27 standard set — documents processed, elements extracted, elements by type, processing duration (ms), errors count.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Extract semantic elements from specification documents using structural analysis (Priority: P1)

A user runs the measurement pipeline on a repository with specification documents. The Deterministic Semantic Engine processes each document through a structured pipeline:

```
Document
    │
    ▼
Markdown Parser  →  AST
    │
    ▼
Visitors  (HeadingVisitor, ListVisitor, TableVisitor, ParagraphVisitor,
           CodeBlockVisitor, QuoteVisitor)
    │
    ▼
Rule Engine  (matches structural observations against rules)
    │
    ▼
Pattern Library  (User Story, GWT, Requirements, Business Rules, etc.)
    │
    ▼
ExtractionResult  (semantic elements + evidence + statistics)
```

All processing is performed offline — no network access, API keys, or external AI services required. The output is a structured ExtractionResult with full evidence provenance.

**Why this priority**: This is the core functionality of the deterministic engine. Without this story, no offline extraction is possible. FR-006 mandates zero external dependencies.

**Independent Test**: Can be fully tested by providing a set of normalized specification documents with known headings, lists, tables, code blocks, and blockquotes — verifying the output contains the expected semantic elements with evidence references.

**Acceptance Scenarios**:

1. **Given** a specification document with headings at multiple levels, **When** the engine processes it, **Then** the output contains semantic elements corresponding to each heading and its hierarchical position.
2. **Given** a document with unordered and ordered lists, **When** the engine processes it, **Then** the output includes list items as semantic observations.
3. **Given** a document with a markdown table, **When** the engine processes it, **Then** the output includes table rows and headers as semantic content.
4. **Given** a document with fenced code blocks, **When** the engine processes it, **Then** the output includes code blocks with their language annotations.
5. **Given** a document with blockquotes, emphasis, and links, **When** the engine processes it, **Then** the output includes observations for each of these structural elements.

---

### User Story 2 - Deterministic extraction produces identical results for identical inputs (Priority: P1)

A user runs the engine twice on the same set of documents. Both runs produce byte-identical ExtractionResult outputs, including element identifiers, confidence scores, and evidence references.

**Why this priority**: NFR-001 requires determinism. Without this guarantee, the platform cannot ensure repeatable measurements, which violates Principles IV and V.

**Independent Test**: Can be tested by processing the same document set twice with the same engine configuration and comparing outputs for byte-identical equality.

**Acceptance Scenarios**:

1. **Given** the same document set is processed by the deterministic engine, **When** extraction runs a second time, **Then** the output is byte-identical to the first run.
2. **Given** identical documents with different in-memory ordering, **When** the engine processes them, **Then** the output order and content remain identical.

---

### User Story 3 - Apply rule-based extraction for common specification patterns (Priority: P1)

A user processes documents containing standard specification patterns: User Stories, Given/When/Then scenarios, Requirement statements (shall/must/should), Business Rules, Actors, Constraints, Assumptions, Decisions, and Glossary Terms. The engine recognizes each pattern and produces typed semantic elements with appropriate confidence scores.

**Why this priority**: FR-008 requires built-in rule support for these patterns. Without pattern recognition, the engine would only produce structural observations without semantic meaning.

**Independent Test**: Can be tested by providing a document with each of the supported pattern types and verifying that the output contains correctly typed and scored elements for each pattern.

**Acceptance Scenarios**:

1. **Given** a document containing a User Story pattern ("As a... I want... So that..."), **When** the engine processes it, **Then** the output includes an element with type "entity" and confidence 0.95.
2. **Given** a document containing "Given/When/Then" scenarios, **When** the engine processes it, **Then** the output includes elements with type "fact" for each scenario step.
3. **Given** a document containing requirement keywords ("Must", "Shall", "Should"), **When** the engine processes it, **Then** the output includes elements with type "fact" for each identified requirement.
4. **Given** a document containing "Actors" as a heading, **When** the engine processes it, **Then** the output includes an Actor Section element with confidence 1.00.

---

### User Story 4 - Extend the engine with custom rule packs (Priority: P2)

A team has a domain-specific specification pattern not covered by built-in rules (e.g., "Security Constraint"). They create a new rule pack file and load it into the engine. The engine applies the custom rules alongside built-in rules, using priority-based conflict resolution.

**Why this priority**: FR-008 requires an extensible rule library. Principle IX (Rule Externalization) mandates that organizational policies remain external to the platform.

**Independent Test**: Can be tested by creating a custom rule pack YAML file with a new pattern, processing a document that contains that pattern, and verifying the output includes correctly typed elements from the custom rule.

**Acceptance Scenarios**:

1. **Given** a custom rule with priority 80 conflicts with a built-in rule with priority 50 on the same content, **When** the engine processes the document, **Then** the custom rule's element is produced and the conflict is logged.
2. **Given** a rule pack with a syntax error, **When** the engine loads it, **Then** the invalid rule is skipped with a logged warning and the remaining rules are applied.

---

### Edge Cases

- What happens if a document contains no recognizable structural patterns? The engine produces an empty ExtractionResult and continues.
- How does the system handle documents with deeply nested headings (10+ levels)? The engine processes up to a maximum heading depth and flattens beyond it.
- What happens if a rule pack file is missing or inaccessible? The engine logs a warning and continues with the remaining loaded rule packs.
- How does the engine handle binary or non-text content? The engine performs a content-type sanity check and skips non-text content with a logged warning.

## Constitution Check *(mandatory)*

**Engaged Principles**: I (Specification First), III (Semantic Before Structural), IV (LLM-Assisted, Deterministic Results), V (Evidence First), VII (Canonical Representation), IX (Rule Externalization), XIV (Layer Independence)

**Compliance Notes**:
- Specification First (I): The engine consumes normalized Document objects from the Specification Adapter layer — it operates on specifications, never on source code.
- Semantic Before Structural (III): The engine transforms Markdown document structure into canonical semantic elements, identifying functional meaning through rule-based pattern recognition.
- LLM-Assisted, Deterministic Results (IV): The engine performs ALL extraction without LLMs. It demonstrates the deterministic side of Principle IV — all measurement inputs are produced by explicit counting rules, not AI inference.
- Evidence First (V): Every extracted element carries an EvidenceReference with document ID, section identifier, and source text fragment. Evidence is mandatory.
- Canonical Representation (VII): The engine produces ExtractionResult in the canonical model defined by F27. No downstream component depends on deterministic-specific artifacts.
- Rule Externalization (IX): Extraction rules are organized as external rule packs (YAML) loaded at engine initialization. Organizations add custom rules without modifying engine code.
- Layer Independence (XIV): The engine implements the SemanticExtractionEngine interface (F27). The pipeline invokes only this interface. No layer knows whether the engine is deterministic or LLM-assisted.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Deterministic Semantic Engine MUST implement the `SemanticExtractionEngine` interface as defined by F27.
- **FR-002**: The engine MUST perform extraction without any external services — no network access, API keys, or AI services.
- **FR-003**: The engine MUST parse documents using a Markdown AST parser and MUST NOT rely on regular expressions as the primary parsing mechanism.
- **FR-004**: The engine MUST traverse the AST using dedicated visitor classes for at least: headings, lists, tables, paragraphs, fenced code blocks, and blockquotes.
- **FR-005**: The engine MUST apply a rule engine that transforms structural observations into typed semantic elements.
- **FR-006**: The engine MUST include a pattern library that recognizes at least: User Story patterns, Given/When/Then scenarios, Requirement statements (shall/must/should), and Business Rules (if/then).
- **FR-007**: The engine MUST support framework-aware extraction rules for at least OpenSpec and SpecKit conventions.
- **FR-008**: The engine MUST generate evidence references for every extracted element, including: document identifier, section identifier, original text fragment, and the extraction rule identifier that produced the element.
- **FR-009**: The engine MUST assign deterministic confidence scores: explicit heading match (1.00), framework convention (0.95), structural heuristic (0.85), pattern inference (0.70).
- **FR-010**: Rules MUST be organized into independent rule packs that can be loaded, updated, and extended without modifying the engine core.
- **FR-011**: The engine MUST produce byte-identical ExtractionResult objects when processing identical inputs with identical rules.
- **FR-012**: The engine MUST process documents in linear time relative to document size.
- **FR-013**: New rule packs MUST be addable without modifying existing rule packs or the engine source code.
- **FR-014**: The engine MUST assign deterministic content-hash IDs to every extracted element, using the F27 canonical scheme: `sha256(f"{document_id}::{section}::{text}")[:16]`.

### Key Entities *(include if feature involves data)*

- **DeterministicSemanticEngine**: The concrete implementation of SemanticExtractionEngine that performs extraction via structural analysis. Operates without any external services.
- **AST Visitor**: A class that traverses the Markdown AST and collects structural observations for a specific token type (e.g., HeadingVisitor, ListVisitor, TableVisitor, CodeBlockVisitor, QuoteVisitor).
- **ExtractionRule**: A rule definition in a rule pack that maps a structural pattern to a typed semantic element. Includes id, name, pattern definition, semantic type, confidence score, and numeric priority (1–100). On conflict, highest priority wins; ties broken by rule ID lexicographic order.
- **RulePack**: A collection of ExtractionRules stored as an external file (YAML). Multiple rule packs can be loaded simultaneously; conflicts resolved by numeric priority score (1–100). Example rule packs include: General Markdown, OpenSpec, SpecKit, BDD, User Stories, Business Rules, Requirements.
- **PatternLibrary**: The collection of built-in and loaded rule packs that the rule engine uses to match structural observations to semantic elements.
- **ExtractedElement**: A single semantic element with a deterministic content-hash ID (`sha256(f"{document_id}::{section}::{text}")[:16]`), semantic type, content, confidence score, and evidence reference — matching the F27 canonical model.
- **ExtractionResult**: The canonical output model (defined by F27) containing extracted elements, evidence references, and processing statistics (documents processed, elements extracted, elements by type, duration in ms, errors count).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A repository with 10 specification documents containing headings, lists, tables, code blocks, and blockquotes is fully extracted in under 5 seconds — no network access or API keys required.
- **SC-002**: Processing the same 10-document set twice produces byte-identical ExtractionResult output across both runs.
- **SC-003**: Every extracted element includes a non-empty evidence reference with document ID and source text fragment.
- **SC-004**: A document containing a User Story, Given/When/Then scenario, Requirement statement, and Business Rule produces correctly typed elements for each pattern with confidence scores matching the RFC-031 table.
- **SC-005**: A new rule pack can be added and applied by placing a YAML file in the rule packs directory — no engine code changes, recompilation, or restart required.

## Out of Scope

This specification does not define:

- **LLM reasoning**: The deterministic engine does not attempt to reproduce or substitute LLM-based semantic inference. Implicit relationships, missing concepts, and enriched entity classification are outside its scope.
- **Heuristic algorithms**: The specific implementation of AST traversal, pattern matching, and rule matching algorithms is defined in the planning phase, not in this specification.
- **Framework-specific extraction plugins**: OpenSpec and SpecKit framework rules are referenced as built-in rule packs but their detailed extraction logic is specified independently.

## Assumptions

- A Markdown AST parser is available and produces a traversable tree or token stream compatible with the visitor pattern.
- Input documents are already normalized by the Specification Adapter layer as Document objects with text content and document type metadata.
- The canonical ExtractionResult model from F27 is stable and available as the output contract.
- Rule packs are stored as YAML files with a well-documented schema; invalid entries are skipped with logged warnings.
- The deterministic engine is invoked only through the SemanticExtractionEngine interface — it has no public API beyond extract().
- Framework-specific rules (OpenSpec, SpecKit) are optional and loaded only when the corresponding rule pack files are present.
- The engine processes one document at a time; document-level parallelism, if needed, is handled by the pipeline layer.

## Future Work

Future deterministic capabilities may extend the rule library without changing the Semantic Extraction Engine interface (F27):

- **Glossary linking**: Automatically linking glossary terms to their definitions across documents.
- **Terminology normalization**: Normalizing synonymous terms to canonical forms.
- **Document cross-references**: Detecting and tracking references between specification documents.
- **Consistency checks**: Validating that related specifications do not contain contradictory statements.
- **Ambiguity detection**: Identifying vague or ambiguous language in specification statements.
- **Duplicate requirement detection**: Finding requirements that appear in multiple locations with similar wording.
- **Structural quality analysis**: Assessing specification structure quality (completeness of sections, adherence to templates).
