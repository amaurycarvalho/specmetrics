# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.1] — 2026-07-17

### [027-semantic-extraction-engine](specs/027-semantic-extraction-engine) Semantic Extraction Engine — unified abstraction layer decoupling the measurement pipeline from any specific semantic extraction strategy

#### Added

- Create `specmetrics/kernel/semantic_extraction_engine.py` — `SemanticExtractionEngine` Protocol and `SemanticEngineFactory`
- Create `specmetrics/kernel/deterministic_engine.py` — `DeterministicSemanticEngine` skeleton
- Create `specmetrics/kernel/litellm_engine.py` — `LiteLLMSemanticEngine` skeleton
- Create `specmetrics/kernel/engine_rule.py` — `ExtractionRule` model and `RulePackLoader`
- Create `specmetrics/kernel/engine_visitors.py` — 8 AST visitor classes (HeadingVisitor, ListVisitor, TableVisitor, CodeBlockVisitor, QuoteVisitor, EmphasisVisitor, LinkVisitor, ParagraphVisitor)
- Create `specmetrics/kernel/engine_patterns.py` — `PatternLibrary` with built-in rule pack
- Create `ExtractedElement`, `EvidenceReference`, `ProcessingStats`, `ExtractionResult` Pydantic models
- Implement `DeterministicSemanticEngine.extract()` with markdown-it-py AST parsing, visitor orchestration, and rule matching
- Implement `LiteLLMSemanticEngine` with LLM prompt construction, response parsing, and failure handling
- Implement rule matching engine with priority-based conflict resolution
- Implement custom rule pack loading via `extra_rule_packs` config
- Create default rule pack YAML at `specmetrics/kernel/rules/default_rule_pack.yaml`
- Add content-hash ID generation (`sha256` fingerprint)
- Add `ProcessingStats` generation and evidence reference mapping with `rule_id`
- Add unit, contract, and integration tests for all phases

#### Changed

- Update `specmetrics/kernel/__init__.py` — export all new kernel classes
- Update `SemanticEngineFactory` — full provider resolution for all 5 LLM providers

#### Fixed

- Fix byte-identical output for SC-002 — add `deterministic_dump()` method excluding timing

### [028-deterministic-semantic-engine](specs/028-deterministic-semantic-engine) DeterministicSemanticEngine — offline-capable implementation of the SemanticExtractionEngine interface

#### Added

- Create `specmetrics/kernel/deterministic_engine.py` — `DeterministicSemanticEngine` with markdown-it-py parsing
- Create `specmetrics/kernel/engine_rule.py` — `ExtractionRule` model and `RulePackLoader` with YAML validation
- Create `specmetrics/kernel/engine_visitors.py` — 9 AST visitors (HeadingVisitor, ListVisitor, TableVisitor, ParagraphVisitor, CodeBlockVisitor, QuoteVisitor, EmphasisVisitor, LinkVisitor)
- Create `specmetrics/kernel/engine_patterns.py` — `PatternLibrary` with priority-based matching
- Create `specmetrics/kernel/rules/` directory with default, OpenSpec, and SpecKit rule packs
- Implement `EvidenceReference` generation with `rule_id` field
- Implement content-hash ID generation and `ProcessingStats`
- Add configurable `max_heading_depth` and binary content detection
- Implement custom rule pack merge with priority-based conflict resolution
- Add framework-specific rule packs for OpenSpec and SpecKit detection
- Create unit and integration tests

#### Changed

- Update `specmetrics/kernel/__init__.py` — export `DeterministicSemanticEngine`

[Unreleased]: https://github.com/amaurycarvalho/specmetrics/compare/v0.3.1...HEAD
[0.3.1]: https://github.com/amaurycarvalho/specmetrics/releases/tag/v0.3.1

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
