# Feature Specification: Canonical Functional Model Builder

**Feature Branch**: `007-canonical-functional-model`

**Created**: 2026-07-15

**Status**: Draft

**Input**: User description: "F06"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Transform evidence graph into canonical functional model (Priority: P1)

A pipeline operator runs the measurement pipeline. After the Evidence Graph stage completes, the CFM Builder automatically transforms the evidence graph into a framework-independent Canonical Functional Model containing Actors, Functional Processes, Business Rules, Data Groups, Relationships, and Operations. The output is free of any SDD framework-specific concepts.

**Why this priority**: This is the core transformation stage that enforces Principle VII (Canonical Representation). Without this stage, downstream measurement engines would depend on framework-specific schemas, violating architectural layering.

**Independent Test**: Can be fully tested by providing a known evidence graph with diverse semantic elements, running the CFM Builder, and verifying that every element is correctly classified into the appropriate CFM category with no framework-specific artifacts present.

**Acceptance Scenarios**:

1. **Given** an evidence graph containing facts about user registration, entities (User, Account), and a relationship (User creates Account), **When** the CFM Builder transforms the graph, **Then** the resulting CFM contains a Functional Process "User Registration", an Actor "User", a Data Group "Account", and a Relationship "User creates Account".
2. **Given** an evidence graph that includes a framework-specific concept (e.g., "OpenSpec Section" or "SpecKit Document"), **When** the CFM Builder transforms the graph, **Then** the resulting CFM contains no nodes or edges labeled with framework-specific terminology.
3. **Given** an evidence graph with evidence references on each node, **When** the CFM Builder processes it, **Then** every element in the resulting CFM preserves its evidence references (document ID, section ID, text fragment), maintaining full traceability.

---

### User Story 2 - Verify CFM correctness via inspection (Priority: P1)

A developer or analyst inspects the generated CFM to verify that semantic elements have been correctly normalized. They can enumerate all Actors, Functional Processes, Business Rules, Data Groups, Relationships, and Operations defined in the model, and trace each one back to its originating evidence.

**Why this priority**: Trust in downstream measurements depends on the correctness of the CFM. Users must be able to validate the normalization before measurements are computed.

**Independent Test**: Can be tested by inspecting the CFM output for a known input graph and verifying that each category contains the expected elements with correct evidence references.

**Acceptance Scenarios**:

1. **Given** a CFM built from an evidence graph, **When** an analyst queries for all Actors in the model, **Then** the response includes only Actor-type elements, each with its evidence reference.
2. **Given** a CFM containing a Functional Process, **When** the analyst traces its constituent Operations, **Then** each Operation is returned with its evidence reference and relationship to the parent Functional Process.
3. **Given** a CFM containing a Business Rule, **When** the analyst inspects its evidence chain, **Then** the rule is traceable through the evidence graph back to the original specification text.

---

### User Story 3 - CFM feeds downstream consumers (Priority: P2)

A measurement engine plugin developer implements a measurement methodology (e.g., FPA Function Point Analysis) that consumes the CFM. They depend on the CFM's stable, documented structure and never need to know which SDD framework originated the specification.

**Why this priority**: Principle VIII (Plugin-Oriented) requires that measurement engines be independent of framework specifics. The CFM is the contract that enables this independence.

**Independent Test**: Can be tested by writing a mock consumer that reads the CFM and verifies all categories are populated and accessible through a defined interface, without any framework-specific imports or knowledge.

**Acceptance Scenarios**:

1. **Given** a CFM with populated Actors, Functional Processes, and Data Groups, **When** a downstream consumer reads the model, **Then** it receives all elements through a documented interface without any reference to OpenSpec, SpecKit, or other SDD framework.
2. **Given** a CFM built from specifications written in different SDD frameworks, **When** a downstream consumer processes both, **Then** the CFM structure is identical regardless of the originating framework — only the element content differs.

---

### Edge Cases

- What happens when the evidence graph contains elements with conflicting types (e.g., the same text fragment classified as both a Business Rule and an Operation)? The CFM builder uses a priority-based classification heuristic: Business Rules take precedence over Operations, Functional Processes take precedence over Operations. Conflicting elements are flagged with a warning in the build metadata.
- What happens when an evidence graph element cannot be classified into any CFM category? Unclassified elements are collected into a "References" category and are still preserved with their evidence references, ensuring no data loss. The build metadata records the count and details of unclassified elements.
- What happens when the evidence graph is empty? The CFM Builder produces an empty CFM and the stage completes without error, emitting a CanonicalModelBuilt event with zero counts.

## Constitution Check *(mandatory)*

**Engaged Principles**: VII (Canonical Representation), XIV (Layer Independence), V (Evidence First)

**Compliance Notes**:
- Canonical Representation (VII): The CFM is the boundary between framework-specific extraction and framework-independent measurement. No framework-specific concept (OpenSpec Section, SpecKit Document, etc.) survives beyond this stage. All downstream components consume only the CFM.
- Layer Independence (XIV): The CFM Builder consumes EvidenceGraph from the Evidence Graph layer and produces CanonicalFunctionalModel for the Rule Pack Engine and Measurement Engine layers. No direct coupling exists between these layers — each communicates through its defined data contract.
- Evidence First (V): Every element in the CFM preserves its evidence references (document ID, section ID, text fragment). No element is created, transformed, or eliminated without maintaining traceability to its source evidence.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The CFM Builder MUST accept an EvidenceGraph (as produced by F05 — Evidence Graph) and produce a CanonicalFunctionalModel containing the following element categories: Actors, Functional Processes, Business Rules, Data Groups, Relationships, and Operations.
- **FR-002**: Each element in the CanonicalFunctionalModel MUST preserve its evidence reference chain: document ID, section ID, and source text fragment from the originating specification.
- **FR-003**: The CanonicalFunctionalModel MUST NOT contain any framework-specific labels, identifiers, or metadata (e.g., no "OpenSpec", "SpecKit", or similar SDD framework references).
- **FR-004**: The CFM Builder MUST classify each evidence graph node into the appropriate CFM category based on its semantic type — fact-type nodes map to Business Rules or Operations, entity-type nodes map to Actors or Data Groups, relationship-type nodes map to Relationships.
- **FR-005**: The CFM Builder MUST handle elements that cannot be classified into any standard category by preserving them in a "References" category with their evidence references intact.
- **FR-006**: The CFM Builder MUST detect and flag conflicting classifications (e.g., same element matching multiple categories) in the build metadata without failing the stage.
- **FR-007**: The CanonicalFunctionalModel MUST be immutable once built — no subsequent stage may modify it in place.
- **FR-008**: The CFM Builder MUST emit a structured event (CanonicalModelBuilt) upon completion, containing model metadata (element count per category, build duration, number of unclassified elements, list of flagged conflicts).
- **FR-009**: The CFM MUST expose a documented interface for downstream consumers to enumerate elements by category, query by evidence reference, and traverse relationships between elements.

### Key Entities *(include if feature involves data)*

- **CanonicalFunctionalModel**: The top-level container for all normalized functional knowledge. Immutable after construction. Contains six named element collections (Actors, Functional Processes, Business Rules, Data Groups, Relationships, Operations) plus a References collection for unclassified elements.
- **Actor**: A person, system, or role that performs or initiates functional processes. Mapped from entity-type nodes with actor semantics in the evidence graph. Preserves evidence references.
- **FunctionalProcess**: A cohesive unit of behavior that delivers value to an Actor. Mapped from operation-type nodes and grouped by relationship context. Contains a collection of constituent Operations.
- **BusinessRule**: A policy, constraint, or condition that governs how a Functional Process operates. Mapped from fact-type nodes with rule semantics. Preserves evidence references.
- **DataGroup**: A logical grouping of related data entities that a Functional Process creates, reads, updates, or deletes. Mapped from entity-type nodes with data semantics.
- **Relationship**: A directed association between two CFM elements (Actors, Functional Processes, Data Groups, etc.). Preserves the relationship type and evidence reference from the source evidence graph.
- **Operation**: A specific action within a Functional Process. Mapped from operation-type nodes that are children of a process-level element. Atomic unit of behavior.
- **BuildMetadata**: A data structure containing diagnostic information about a CFM build: element counts per category, build duration, count of unclassified elements, and list of classification conflicts flagged during the transformation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An evidence graph containing 500 elements across all semantic types is transformed into a CFM in under 3 seconds on a standard development machine.
- **SC-002**: A CFM built from an evidence graph containing framework-specific labels (e.g., "OpenSpec Section") contains zero elements with those labels — all are normalized to canonical categories.
- **SC-003**: Every element in the resulting CFM is traceable to its originating evidence graph node (100% evidence reference preservation).
- **SC-004**: A downstream consumer can enumerate all six CFM element categories through the documented interface without importing any framework-specific module.
- **SC-005**: An evidence graph containing 10 unclassifiable elements produces a CFM where all 10 elements are preserved in the References category with complete evidence references.
- **SC-006**: Building the CFM from identical evidence graphs twice produces identical models (element-for-element and evidence-reference-for-evidence-reference equality).

## Assumptions

- The EvidenceGraph from F05 (Evidence Graph) provides sufficient semantic type information (fact, entity, relationship, operation) for the CFM Builder to perform classification into Actor, FunctionalProcess, BusinessRule, DataGroup, Relationship, and Operation categories.
- Framework-specific labels are identifiable through naming conventions or type markers in the evidence graph — the CFM Builder applies pattern-based detection to strip or normalize them.
- The CFM is an in-memory data structure with serialization support for debugging and inspection — primary deployment is as a pipeline stage, not a standalone service.
- Existing plugin discovery mechanism (F02) is not required for this stage — the CFM Builder is a core pipeline stage, not a plugin extension point.
- The CFM interface may be implemented as abstract base classes or protocols — the downstream consumers depend on the interface contract, not a concrete implementation.
- The Rule Pack Engine (F09) and Measurement Engine (F07) are the primary downstream consumers of the CFM — the interface is designed to serve both.
