# Changelog Archive

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [0.2.0] — 2026-07-16

#### Fixed

- **validation-rules.yml** — Convert sample file `.specmetrics/rules/validation-rules.yml` to valid Rule Pack format (added missing `id` field, restructured as list). The file documents built-in spec quality validation rules but must not break the Rule Pack engine loader. ([#010](specs/010-rule-pack-engine), [#015](specs/015-validation-pipeline))

### [017-measurement-engine-sfp](specs/017-measurement-engine-sfp) Measurement Engine Plugin — Simple Function Points (SFP)

#### Added

- Specification drafted

### [018-measurement-engine-snap](specs/018-measurement-engine-snap) Measurement Engine Plugin — SNAP

#### Added

- Specification drafted

### [019-specification-plugin-openspec](specs/019-specification-plugin-openspec) Specification Plugin — OpenSpec

#### Added

- Specification drafted

### [020-specification-plugin-speckit](specs/020-specification-plugin-speckit) Specification Plugin — SpecKit

#### Added

- Specification drafted

## [0.1.1] — 2026-07-16

#### Fixed

- FPA engine and CLI commands.

## [0.1.0] — 2026-07-16

### [001-mvp-release-outline](specs/001-mvp-release-outline) MVP Release 0.1 Outline

#### Added
- Create dedicated specs for each feature from this catalog

#### Changed
- Understand the full scope of Release 0.1 at a glance
- Track specification and implementation progress
- Identify dependencies between features
- Prioritize development order
- **SC-001**: All 15 features have been decomposed into individual specs under
- **SC-002**: Each feature spec passes its own quality checklist before planning
- **SC-003**: Dependency map is validated — no circular dependencies exist among
- **SC-004**: All P1 features are ready for `/speckit.plan` before any P2
- Feature numbering follows sequential ordering (001, 002, 003...) under `specs/`
- Each feature will be refined independently before implementation
- The release may be descoped if dependency analysis reveals excessive complexity
- SFP and SNAP measurement plugins are deferred to post-MVP releases
- The SpecKit adapter is deferred to post-MVP (OpenSpec adapter scoped for MVP)
- REST API services are deferred to post-MVP (CLI + MCP only)

### [002-kernel-pipeline-engine](specs/002-kernel-pipeline-engine) Implement the Pipeline Engine and Event Bus that orchestrate the SpecMetrics Semantic Measurement Pipeline.

#### Added
- Create `specmetrics/kernel/` and `specmetrics/application/` package directories with `__init__.py`
- Create `specmetrics/kernel/events.py` — EventType enum with all 11 canonical event types
- Create `specmetrics/kernel/exceptions.py` — StageError, PipelineError, HandlerNotFoundError exception classes
- Create `tests/unit/` and `tests/integration/` package directories with `__init__.py`
- Add `structlog` to project dependencies in `pyproject.toml`
- Create `specmetrics/kernel/pipeline_context.py` — PipelineContext dataclass (frozen) with execution_id, all stage output fields as Optional, published_events tuple, diagnostics, and metadata
- Create `specmetrics/kernel/events.py` — PipelineEvent base dataclass (frozen) with event_type, publisher, payload, context, timestamp
- Create `specmetrics/kernel/handler_registry.py` — HandlerRegistry class with register() and resolve() methods, mapping EventType → EventHandler
- Create `specmetrics/kernel/diagnostics.py` — Diagnostics, StageTiming, StageError, ExecutionMetadata dataclasses per data-model.md
- Create `specmetrics/kernel/__init__.py` — Re-export all public types (PipelineContext, PipelineEvent, EventType, EventHandler, StageError)
- Create `specmetrics/kernel/event_bus.py` — EventBus class with publish(event) method, synchronous in-order delivery to registered handler
- Create `specmetrics/kernel/pipeline_engine.py` — PipelineEngine class with run(context) method, orchestrating the canonical event sequence: RepositoryLoaded → DocumentsDiscovered → SemanticExtractionCompleted → EvidenceGraphBuilt → CanonicalModelBuilt → RulePackApplied → MeasurementCompleted → ExportCompleted → TelemetryPublished → PipelineCompleted
- Add `with_stage_output()` builder method to PipelineContext in `specmetrics/kernel/pipeline_context.py`
- Add logging (structlog) for each stage transition in `specmetrics/kernel/pipeline_engine.py`
- Add PipelineEngine.run() to kernel `__init__.py` public API
- Add fail-fast error handling to PipelineEngine.run() — catch StageError, publish PIPELINE_FAILED, halt execution in `specmetrics/kernel/pipeline_engine.py`
- Add validation in HandlerRegistry.resolve() — raise HandlerNotFoundError if no handler registered for event_type in `specmetrics/kernel/handler_registry.py`
- Add edge case: no plugins installed → PipelineEngine.run() fails with descriptive error about missing handlers in `specmetrics/kernel/pipeline_engine.py`
- Add edge case: concurrent pipeline executions produce independent PipelineContext instances in `specmetrics/kernel/pipeline_engine.py`
- Add execution_id generation (UUID v4) to PipelineEngine startup in `specmetrics/kernel/pipeline_engine.py`
- Add diagnostics collection — capture started_at, completed_at, duration_ms, status per stage in PipelineEngine in `specmetrics/kernel/pipeline_engine.py`
- Add StageError capture to diagnostics.errors list on failure in `specmetrics/kernel/pipeline_engine.py`
- Add docstrings to all public kernel classes and methods

#### Changed
- Test: PipelineEngine publishes RepositoryLoaded as first event in `tests/unit/test_pipeline_engine.py`
- Test: PipelineEngine invokes handlers in canonical event order in `tests/unit/test_pipeline_engine.py`
- Test: PipelineEngine returns PipelineCompleted event on success in `tests/unit/test_pipeline_engine.py`
- Test: EventBus delivers events synchronously and in-order in `tests/unit/test_event_bus.py`
- Test: EventBus raises error for unregistered event type in `tests/unit/test_event_bus.py`
- Test: PipelineContext is immutable — with_stage_output returns new instance in `tests/unit/test_pipeline_context.py`
- Integration test: Pipeline with 2 mock stages executes in correct order in `tests/integration/test_pipeline_execution.py`
- Test: StageError in any handler halts pipeline immediately in `tests/unit/test_pipeline_engine.py`
- Test: PIPELINE_FAILED event contains failed_stage and error_message in `tests/unit/test_pipeline_engine.py`
- Test: Unregistered handler raises HandlerNotFoundError at resolution time in `tests/unit/test_handler_registry.py`
- Integration test: Pipeline with failing stage halts before downstream stages in `tests/integration/test_pipeline_execution.py`
- Test: PipelineContext.published_events contains all events in publication order in `tests/unit/test_pipeline_context.py`
- Test: Diagnostics records started_at, completed_at, and status for each stage in `tests/unit/test_pipeline_engine.py`
- Test: Each execution produces unique execution_id (UUID v4) in `tests/unit/test_pipeline_engine.py`
- Integration test: Full pipeline context inspection after execution in `tests/integration/test_pipeline_execution.py`
- Append each published event to PipelineContext.published_events tuple in `specmetrics/kernel/pipeline_engine.py`
- Run quickstart.md validation scenarios end-to-end

### [003-plugin-discovery-registry](specs/003-plugin-discovery-registry) Implement the Plugin Discovery and Registry subsystem that discovers SpecMetrics plugins via Python Entry Points, validates their compatibility, and exposes a registry for the Pipeline Engine (F01) to resolve event handlers.

#### Added
- Create `specmetrics/kernel/plugin_metadata.py` — PluginMetadata frozen dataclass, PluginType enum, PluginStatus enum per data-model.md
- Add `PluginError` exception to `specmetrics/kernel/exceptions.py` for plugin-related failures
- Create `specmetrics/kernel/plugin_metadata.py` — PluginMetadata frozen dataclass with id, api_version, plugin_type, handled_event_types, handler_factory, name, description, author, version
- Create `specmetrics/kernel/plugin_metadata.py` — PluginType enum (ADAPTER, SEMANTIC, MEASUREMENT, EXPORTER, PUBLISHER, UNSPECIFIED)
- Create `specmetrics/kernel/plugin_metadata.py` — PluginStatus enum (PENDING, REGISTERED, REJECTED, SKIPPED)
- Create `specmetrics/kernel/plugin_registry.py` — PluginDescriptor dataclass with metadata, entry_point_name, status, validation_errors
- Create `specmetrics/kernel/plugin_discovery.py` — PluginDiscovery class with scan() method using importlib.metadata.entry_points for the `specmetrics.plugins` group
- Add factory function loading — PluginDiscovery.load() imports the entry point target and calls it to obtain PluginMetadata
- Add `__init__.py` re-export for PluginDiscovery and its public methods
- Create `specmetrics/kernel/plugin_validation.py` — PluginValidator class with validate(metadata) method performing: API version SemVer check, required field presence, handler_factory check
- Add platform API version resolution via `importlib.metadata.version("specmetrics")` in PluginValidator
- Add SemVer comparison logic — major must match; minor/patch within same major accepted; pre-release tags ignored; unparseable rejected
- Add validation result reporting — return structured ValidationResult with is_valid, errors list
- Create `specmetrics/kernel/plugin_registry.py` — PluginRegistry class with: register(), get_handler(), get_handlers(), list_plugins(), get_by_type()
- Add `install_handlers(handler_registry)` method to PluginRegistry — iterates all REGISTERED plugins and calls handler_registry.register() for each handler_factory-produced handler
- Add duplicate plugin ID detection — log warning, overwrite with last registration
- Add per-plugin try/except in PluginDiscovery.scan() — catch import errors and factory errors, log warning with plugin ID, continue to next plugin
- Add per-plugin try/except in PluginRegistry.register() — catch validation errors, set descriptor status to REJECTED, log error
- Add docstrings to all public plugin classes and methods

#### Changed
- Update `specmetrics/kernel/__init__.py` — Export PluginMetadata, PluginType, PluginStatus, PluginError, PluginRegistry, PluginDiscovery
- Test: PluginDiscovery scans `specmetrics.plugins` entry points and returns discovered metadata in `tests/unit/test_plugin_discovery.py`
- Test: PluginDiscovery handles empty discovery (no plugins installed) without errors in `tests/unit/test_plugin_discovery.py`
- Test: PluginDiscovery loads factory function and retrieves PluginMetadata in `tests/unit/test_plugin_discovery.py`
- Test: PluginDiscovery discovers multiple plugins and returns all of them in `tests/unit/test_plugin_discovery.py`
- Test: PluginValidator rejects plugin with incompatible major API version in `tests/unit/test_plugin_validation.py`
- Test: PluginValidator accepts plugin with compatible API version (same major, different minor/patch) in `tests/unit/test_plugin_validation.py`
- Test: PluginValidator rejects plugin with unparseable version string in `tests/unit/test_plugin_validation.py`
- Test: PluginValidator rejects plugin missing required metadata fields in `tests/unit/test_plugin_validation.py`
- Test: PluginValidator checks handler_factory presence when handled_event_types is non-empty in `tests/unit/test_plugin_validation.py`
- Test: PluginRegistry.register() stores a validated PluginDescriptor in `tests/unit/test_plugin_registry.py`
- Test: PluginRegistry.get_handler() returns handler for registered event type in `tests/unit/test_plugin_registry.py`
- Test: PluginRegistry.get_handler() returns None for unregistered event type in `tests/unit/test_plugin_registry.py`
- Test: PluginRegistry.get_handlers() returns all handlers for an event type in registration order in `tests/unit/test_plugin_registry.py`
- Test: PluginRegistry.install_handlers() populates F01 HandlerRegistry correctly in `tests/unit/test_plugin_registry.py`
- Test: PluginRegistry handles duplicate plugin IDs by logging warning and using last registration in `tests/unit/test_plugin_registry.py`
- Integration test: End-to-end plugin lifecycle — discover → validate → register → install handlers → pipeline uses handlers in `tests/integration/test_plugin_lifecycle.py`
- Wire discovery → validation → registry into a unified load_plugins() entry point that performs the full lifecycle
- Update `specmetrics/kernel/__init__.py` — export PluginRegistry and load_plugins
- Test: PluginDiscovery skips a plugin when its factory function raises an exception in `tests/unit/test_plugin_discovery.py`
- Test: PluginDiscovery skips a plugin when its module cannot be imported in `tests/unit/test_plugin_discovery.py`
- Test: load_plugins() isolates errors — one faulty plugin does not prevent healthy plugins from registering in `tests/unit/test_plugin_registry.py`
- Integration test: Healthy plugin registers despite presence of faulty plugin in `tests/integration/test_plugin_lifecycle.py`
- Ensure load_plugins() atomicity — each plugin discovery + validation + registration is isolated; one failure never blocks another
- Run quickstart.md validation scenarios end-to-end

### [004-specification-adapter-interface](specs/004-specification-adapter-interface) Define and implement the Specification Adapter plugin interface that SDD framework adapters must implement.

#### Added
- Create `specmetrics/kernel/adapter_interface.py` — SpecificationAdapter Protocol, Document dataclass, DocumentSection dataclass
- Create `specmetrics/kernel/adapter_registry.py` — AdapterRegistry class wrapping F02 PluginRegistry
- Create `Document` frozen dataclass in `specmetrics/kernel/adapter_interface.py` — id, path, document_type, content, metadata, sections per data-model.md
- Create `DocumentSection` frozen dataclass in `specmetrics/kernel/adapter_interface.py` — id, title, level, content, subsections
- Create `SpecificationAdapter` Protocol in `specmetrics/kernel/adapter_interface.py` — scan() and supports() method signatures with pathlib.Path argument types
- Implement SpecificationAdapter Protocol in `specmetrics/kernel/adapter_interface.py` — structural typing with scan() and supports()
- Implement Document and DocumentSection frozen dataclasses in `specmetrics/kernel/adapter_interface.py`
- Implement file discovery logic — recursive glob for text files (*.md, *.yml, *.yaml) in scan() base implementation in `specmetrics/kernel/adapter_interface.py`
- Implement per-document error isolation — try/except for each file read, skip failures, log warning in `specmetrics/kernel/adapter_interface.py`
- Add document type inference helper — map parent directory names to canonical types in `specmetrics/kernel/adapter_interface.py`
- Create `AdapterRegistry` class in `specmetrics/kernel/adapter_registry.py` — wraps F02 PluginRegistry, provides find_adapter(), list_adapters(), scan_all()
- Implement find_adapter() — iterates registered adapters calling supports() on each, returns first match
- Implement scan_all() — runs scan() on all adapters that support the given path
- Add adapter routing — find_adapter() tries adapters in registration order, returns first match
- Add docstrings to all public adapter classes and methods

#### Changed
- Update `specmetrics/kernel/__init__.py` — Export SpecificationAdapter, Document, DocumentSection, AdapterRegistry
- Test: A class implementing SpecificationAdapter Protocol passes isinstance check in `tests/unit/test_adapter_interface.py`
- Test: A class missing scan() does NOT pass Protocol check in `tests/unit/test_adapter_interface.py`
- Test: A class missing supports() does NOT pass Protocol check in `tests/unit/test_adapter_interface.py`
- Test: Mock adapter scan() returns all discovered documents in `tests/unit/test_adapter_interface.py`
- Test: Mock adapter returns empty list for empty repository in `tests/unit/test_adapter_interface.py`
- Test: Document dataclass accepts valid field values in `tests/unit/test_adapter_interface.py`
- Test: Document preserves metadata dict in `tests/unit/test_adapter_interface.py`
- Test: DocumentSection stores hierarchy correctly (parent section with nested subsections) in `tests/unit/test_adapter_interface.py`
- Test: Document with empty content is valid in `tests/unit/test_adapter_interface.py`
- Test: Mock adapter scan() returns Documents with correct path and type fields in `tests/unit/test_adapter_interface.py`
- Test: AdapterRegistry.list_adapters() returns all registered adapters in `tests/unit/test_adapter_registry.py`
- Test: AdapterRegistry.find_adapter() returns correct adapter for a matching path in `tests/unit/test_adapter_registry.py`
- Test: AdapterRegistry.find_adapter() returns None when no adapter supports the path in `tests/unit/test_adapter_registry.py`
- Test: AdapterRegistry.scan_all() returns results from multiple adapters in `tests/unit/test_adapter_registry.py`
- Integration test: Mock adapter registered via F02 plugin mechanism is available through AdapterRegistry in `tests/integration/test_adapter_pipeline.py`
- Integration test: Adapter scan() output is consumable by PipelineEngine in `tests/integration/test_adapter_pipeline.py`
- Update `specmetrics/kernel/__init__.py` — export AdapterRegistry
- Test: Two adapters registered, find_adapter() returns correct one for each path in `tests/unit/test_adapter_registry.py`
- Test: scan_all() with two adapters returns combined results in `tests/unit/test_adapter_registry.py`
- Integration test: Two adapters coexist and each processes its own documents in `tests/integration/test_adapter_pipeline.py`
- Ensure AdapterRegistry supports multiple adapters of same type — no deduplication by adapter id in `specmetrics/kernel/adapter_registry.py`
- Run quickstart.md validation scenarios end-to-end

### [005-semantic-extraction](specs/005-semantic-extraction) Implement the Semantic Extraction pipeline stage (F04) that consumes normalized Document objects from the Specification Adapter layer and produces extracted semantic elements (facts, entities, relationships, operations) with evidence provenance.

#### Added
- Create `specmetrics/kernel/extraction_provider.py` — ExtractionProvider Protocol, ExtractedElement model, EvidenceReference model, ExtractionResult model, ProcessingStats model
- Create `specmetrics/kernel/extraction_registry.py` — ProviderRouter class for document-type to provider mapping
- Create `specmetrics/kernel/extraction_stage.py` — ExtractionStage EventHandler skeleton (placeholder handle method)
- Create `ExtractedElement` Pydantic model in `specmetrics/kernel/extraction_provider.py` — id, type (fact/entity/relationship/operation), confidence (0.0–1.0), evidence (EvidenceReference), content per data-model.md
- Create `EvidenceReference` Pydantic model in `specmetrics/kernel/extraction_provider.py` — document_id, section_id (optional), text
- Create `ExtractionResult` and `ProcessingStats` Pydantic models in `specmetrics/kernel/extraction_provider.py`
- Create `ExtractionProvider` Protocol in `specmetrics/kernel/extraction_provider.py` — extract() and supports_type() method signatures
- Implement ExtractionProvider Protocol in `specmetrics/kernel/extraction_provider.py` — structural typing with extract() and supports_type()
- Implement ProviderRouter in `specmetrics/kernel/extraction_registry.py` — resolve document types to providers, register providers with optional type overrides
- Implement ExtractionStage in `specmetrics/kernel/extraction_stage.py` — EventHandler for DOCUMENTS_DISCOVERED, iterates documents and delegates to resolved providers, consolidates results
- Implement EvidenceReference validation — document_id and text must be non-empty in `specmetrics/kernel/extraction_provider.py`
- Implement ProviderRouter.resolve() — iterates registered providers calling supports_type(), returns first match in `specmetrics/kernel/extraction_registry.py`
- Implement F02 plugin discovery integration — extraction providers with plugin_type SEMANTIC are discovered and registered with ProviderRouter in `specmetrics/kernel/extraction_registry.py`
- Implement built-in LLM-assisted extraction provider in `specmetrics/plugins/semantic/llm_provider.py` — uses LiteLLM gateway, graceful degradation to structural parsing, supports all document types
- Add docstrings to all public extraction classes and methods

#### Changed
- Update `specmetrics/kernel/__init__.py` — Export ExtractionProvider, ExtractedElement, EvidenceReference, ExtractionResult, ProcessingStats, ProviderRouter, ExtractionStage
- Test: A class implementing ExtractionProvider Protocol passes structural check in `tests/unit/test_extraction_provider.py`
- Test: A class missing extract() does NOT pass Protocol check in `tests/unit/test_extraction_provider.py`
- Test: A class missing supports_type() does NOT pass Protocol check in `tests/unit/test_extraction_provider.py`
- Test: ExtractionStage handles DOCUMENTS_DISCOVERED event and returns ExtractionResult in `tests/unit/test_extraction_stage.py`
- Test: ExtractionStage routes documents to correct provider based on document_type in `tests/unit/test_extraction_stage.py`
- Test: ExtractionStage processes multiple documents and consolidates results in `tests/unit/test_extraction_stage.py`
- Test: EvidenceReference accepts valid document_id and text in `tests/unit/test_extraction_provider.py`
- Test: ExtractedElement requires valid evidence reference in `tests/unit/test_extraction_provider.py`
- Test: ExtractionStage output includes evidence references for each element in `tests/unit/test_extraction_stage.py`
- Integrate evidence provenance into ExtractionStage — each ExtractedElement from a provider carries provider-assigned evidence, stage verifies evidence completeness in `specmetrics/kernel/extraction_stage.py`
- Test: ProviderRouter.register() stores provider for document type in `tests/unit/test_extraction_registry.py`
- Test: ProviderRouter.resolve() returns correct provider for matching type in `tests/unit/test_extraction_registry.py`
- Test: ProviderRouter.resolve() returns None when no provider matches in `tests/unit/test_extraction_registry.py`
- Integration test: Mock provider registered via F02 plugin mechanism is available through ProviderRouter in `tests/integration/test_extraction_pipeline.py`
- Update `specmetrics/kernel/__init__.py` — ensure ProviderRouter is exported
- Test: Built-in LLM provider handles documents with valid LiteLLM response in `tests/unit/test_llm_provider.py`
- Test: Built-in LLM provider degrades gracefully when LLM unavailable in `tests/unit/test_llm_provider.py`
- Integration test: Full pipeline with built-in provider produces ExtractionResult in `tests/integration/test_extraction_pipeline.py`
- Register built-in provider as default in ProviderRouter — automatically available when no explicit routing configured in `specmetrics/kernel/extraction_registry.py`
- Run quickstart.md validation scenarios end-to-end

### [006-evidence-graph-store](specs/006-evidence-graph-store) Build the Evidence Graph pipeline stage — the fourth stage in the SpecMetrics measurement pipeline.

#### Added
- Create `specmetrics/kernel/evidence_graph.py` — EvidenceGraph structure with NodeAlreadyExistsError, NodeNotFoundError, EdgeAlreadyExistsError, SelfLoopError, InvalidGraphDataError exception classes
- Create `specmetrics/kernel/graph_query_engine.py` — GraphQueryEngine skeleton class
- Create `specmetrics/kernel/graph_persistence.py` — GraphStore skeleton class
- Create `specmetrics/kernel/evidence_graph_stage.py` — EvidenceGraphStage EventHandler skeleton (placeholder handle method)
- Create `GraphNode` Pydantic model in `specmetrics/kernel/evidence_graph.py` — id, node_type (extracted_element/evidence), semantic_type (fact/entity/relationship/operation, optional), document_id, section_id (optional), text, confidence (optional), element_id (optional) per data-model.md
- Create `GraphEdge` Pydantic model in `specmetrics/kernel/evidence_graph.py` — source, target, edge_type (derived_from/references/composed_of), metadata (optional dict)
- Create `GraphMetadata` Pydantic model in `specmetrics/kernel/evidence_graph.py` — run_id, node_count, edge_count, documents_covered, created_at, pipeline_version (optional)
- Create `GraphBackend` Protocol in `specmetrics/kernel/evidence_graph.py` — add_node(), add_edge(), get_node(), query_nodes(), traverse(), to_serializable(), from_serializable() per contracts/graph-backend-protocol.md
- Create `EvidenceGraph` root model in `specmetrics/kernel/evidence_graph.py` — run_id, nodes (dict), edges (list[GraphEdge]), metadata (GraphMetadata)
- Implement `NetworkXBackend` in `specmetrics/kernel/evidence_graph.py` — wraps networkx.DiGraph, implements GraphBackend Protocol
- Implement NetworkXBackend in `specmetrics/kernel/evidence_graph.py` — add_node, add_edge, get_node, query_nodes, traverse, to_serializable, from_serializable with all validation rules from the contract
- Implement EvidenceGraph node identity fingerprint function — SHA-256 of (document_id, section_id, text, semantic_type) in `specmetrics/kernel/evidence_graph.py`
- Implement EvidenceGraphStage.handle() — receives ExtractionResult, creates graph nodes for each ExtractedElement and EvidenceReference, links via derived_from edges, deduplicates by fingerprint, populates GraphMetadata in `specmetrics/kernel/evidence_graph_stage.py`
- Implement GraphQueryEngine.query_by_document() in `specmetrics/kernel/graph_query_engine.py`
- Implement GraphQueryEngine.query_by_type() in `specmetrics/kernel/graph_query_engine.py`
- Implement GraphQueryEngine.query_by_evidence() in `specmetrics/kernel/graph_query_engine.py`
- Implement GraphQueryEngine.traverse_provenance() in `specmetrics/kernel/graph_query_engine.py`
- Implement GraphQueryEngine.find_references() in `specmetrics/kernel/graph_query_engine.py`
- Implement GraphStore.save() in `specmetrics/kernel/graph_persistence.py`
- Implement GraphStore.load() in `specmetrics/kernel/graph_persistence.py`
- Implement GraphStore.list_graphs() in `specmetrics/kernel/graph_persistence.py`
- Implement GraphStore.delete() in `specmetrics/kernel/graph_persistence.py`
- Implement EvidenceGraphStage.update_for_document() in `specmetrics/kernel/evidence_graph_stage.py`
- Implement incremental update mode in EvidenceGraphStage.handle() — detect if graph exists, route to full build vs incremental update, auto-save after update in `specmetrics/kernel/evidence_graph_stage.py`
- Add docstrings to all public evidence graph classes and methods

#### Changed
- Update `specmetrics/kernel/__init__.py` — Export all new classes
- Test: NetworkXBackend.add_node() stores node with correct attributes in `tests/unit/test_evidence_graph.py`
- Test: NetworkXBackend.add_node() raises NodeAlreadyExistsError for duplicate IDs in `tests/unit/test_evidence_graph.py`
- Test: NetworkXBackend.add_edge() raises NodeNotFoundError for missing source in `tests/unit/test_evidence_graph.py`
- Test: NetworkXBackend.add_edge() raises SelfLoopError for source==target in `tests/unit/test_evidence_graph.py`
- Test: NetworkXBackend.get_node() returns correct node attributes in `tests/unit/test_evidence_graph.py`
- Test: NetworkXBackend.get_node() returns None for non-existent ID in `tests/unit/test_evidence_graph.py`
- Test: NetworkXBackend.to_serializable() / from_serializable() round-trip preserves graph structure in `tests/unit/test_evidence_graph.py`
- Test: Building graph from valid ExtractionResult produces correct node count and edge count in `tests/unit/test_evidence_graph.py`
- Test: query_by_document returns all and only nodes from the specified document in `tests/unit/test_graph_query_engine.py`
- Test: query_by_type returns nodes of the correct semantic type in `tests/unit/test_graph_query_engine.py`
- Test: query_by_evidence matches text fragments correctly in `tests/unit/test_graph_query_engine.py`
- Test: traverse_provenance traces from element back through evidence chain in `tests/unit/test_graph_query_engine.py`
- Test: traverse_provenance with max_depth stops at correct depth in `tests/unit/test_graph_query_engine.py`
- Test: traverse_provenance handles cyclic graphs without infinite loops in `tests/unit/test_graph_query_engine.py`
- Test: find_references returns both forward and backward related nodes in `tests/unit/test_graph_query_engine.py`
- Wire GraphQueryEngine into EvidenceGraphStage — expose query methods on the stage output in `specmetrics/kernel/evidence_graph_stage.py`
- Test: JSONL save writes metadata, nodes, and edges in correct format in `tests/unit/test_graph_persistence.py`
- Test: JSONL load reconstructs identical graph with all nodes and edges in `tests/unit/test_graph_persistence.py`
- Test: Loading corrupted JSONL file raises InvalidGraphDataError in `tests/unit/test_graph_persistence.py`
- Test: list_graphs returns only valid graph files in `tests/unit/test_graph_persistence.py`
- Test: Save is atomic — interruption leaves no partial file in `tests/unit/test_graph_persistence.py`
- Test: GraphStore round-trip produces node-for-node, edge-for-edge identical graph in `tests/unit/test_graph_persistence.py`
- Integrate persistence into EvidenceGraphStage — auto-save after build in `specmetrics/kernel/evidence_graph_stage.py`
- Test: Incremental update replaces nodes from specified document in `tests/unit/test_evidence_graph.py`
- Test: Incremental update preserves nodes from other documents in `tests/unit/test_evidence_graph.py`
- Test: Incremental update with empty replacement removes all nodes for that document in `tests/unit/test_evidence_graph.py`
- Integration test: Full pipeline with incremental update produces correct graph state in `tests/integration/test_evidence_graph_pipeline.py`
- Run quickstart.md validation scenarios end-to-end

### [007-canonical-functional-model](specs/007-canonical-functional-model) Build the Canonical Functional Model (CFM) pipeline stage — the fifth stage in the SpecMetrics measurement pipeline.

#### Added
- Create `specmetrics/kernel/cfm/` package directory with `__init__.py`
- Create test directories: `tests/unit/`, `tests/contract/`, `tests/integration/`
- Create CFM entity models
- Create `BuildMetadata` and `ClassificationConflict` types
- Create `EvidenceRef` value object
- Create type aliases
- Write unit tests for classification and builder
- Implement classification logic and framework label detection
- Implement `build()` and pipeline stage
- Implement query methods and relationship traversal
- Write contract and integration tests
- Implement CFM serialization

#### Changed
- Handle edge cases in builder
- Define `CFMConsumer` protocol
- Ensure immutability (frozen=True)
- Register with `HandlerRegistry`
- Wire event emission
- Run all tests and quickstart

### [008-measurement-engine-fpa](specs/008-measurement-engine-fpa) Implement a deterministic IFPUG/FPA function point measurement engine as a discoverable plugin.

#### Added
- Create plugin package structure
- Implement complexity matrices
- Implement `FPACounter`, `MeasurementExplainer`, `RulePackApplicator`
- Implement `FPAMeasurementPlugin` class
- Implement determinism verification

#### Changed
- Define FPA models and tests
- Wire measurement flow and Rule Pack integration
- Register entry point and event emission
- Run quickstart and update checklists

### [009-cli-mcp-interface](specs/009-cli-mcp-interface) Provide both human (CLI) and machine (MCP) interfaces.

#### Added
- Create CLI, MCP, and application packages
- Implement pipeline request/result models
- Create Typer app with measure, plugins, version commands
- Implement CLI output formatters
- Implement MCP server with stdio transport
- Implement MCP tools (measure, plugins_list, version)

#### Changed
- Wire orchestrator into CLI and MCP
- Wire config loading and plugin discovery
- Verify CLI/MCP parity
- Run quickstart

### [010-rule-pack-engine](specs/010-rule-pack-engine) Rule Pack Engine pipeline stage.

#### Added
- Create plugin structure
- Implement loader, validator, applicator, annotator
- Add logging and tests

#### Changed
- Register entry point and wire into pipeline
- Validate quickstart scenarios

### [011-export-layer](specs/011-export-layer) Publication Layer — exporters and publishers.

#### Added
- Create exporter/publisher structure
- Implement JSON, CSV, XML exporters
- Implement CLI and MCP export commands
- Implement OpenTelemetry publisher

#### Changed
- Register entry points
- Integrate with pipeline and handle errors
- Run quickstart

### [012-opentelemetry-publisher](specs/012-opentelemetry-publisher) OpenTelemetry metrics publisher.

#### Added
- Create publisher structure
- Implement configuration, metrics conversion, batching, retry
- Add tests

#### Changed
- Register plugin and wire into pipeline
- Run quickstart

### [013-mcp-server](specs/013-mcp-server) Standalone MCP server.

#### Added
- Create MCP package with server, transport, registry
- Implement tools, resources, prompts
- Implement lifecycle management

#### Changed
- Register tools and resources
- Run quickstart and verify SC-006

### [014-configuration-system](specs/014-configuration-system) Configuration System

#### Changed
- Configuration loading from hierarchy
- Schema validation, YAML/JSON support
- Plugin schema registration
- Configuration dump with provenance
- Sensitive value masking

### [015-validation-pipeline](specs/015-validation-pipeline) Pre-measurement validation gate

#### Added
- Create validation package
- Implement FORMAT, STRUCTURAL, CONSTITUTIONAL rules
- Implement CLI command with batch mode

#### Changed
- Integrate into pipeline engine
- Run quickstart

### [016-explain-measurement](specs/016-explain-measurement) Measurement explanation capability

#### Added
- Create explanation package
- Implement ExplainService, EvidenceTracer
- Implement comparison logic
- Create CLI and MCP tools

#### Changed
- Run quickstart

## [0.0.0] — 2026-07-15

[0.2.0]: https://github.com/amaurycarvalho/specmetrics/releases/tag/v0.2.0
[0.1.1]: https://github.com/amaurycarvalho/specmetrics/releases/tag/v0.1.1
[0.1.0]: https://github.com/amaurycarvalho/specmetrics/releases/tag/v0.1.0
[0.0.0]: https://github.com/amaurycarvalho/specmetrics/releases/tag/v0.0.0

See main [CHANGELOG](CHANGELOG.md) for newer releases.
