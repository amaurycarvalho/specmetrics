# Research: Specialized Deterministic Fallbacks

**Branch**: `029-deterministic-fallback-specialists` | **Date**: 2026-07-18

## Extraction Strategy

**Decision**: Regex-based extraction using framework-specific YAML rule packs

**Rationale**: Speckit and OpenSpec documents follow consistent template patterns (section headings, keyword markers, structured lists). Regex targeting these patterns captures sufficient semantic content for CFM/CSM population. The existing deterministic engine already supports rule confidence scoring to filter low-quality matches.

**Alternatives considered**: Full Markdown AST parsing — would provide more structural precision but requires a parser per Markdown dialect and prevents external rule customization via YAML.

## Framework Detection

**Decision**: Auto-detect via `document.document_type` metadata from the Specification Adapter

**Rationale**: The existing `_load_framework_packs()` mechanism already distinguishes document types. No changes to adapter metadata are needed.

**Alternatives considered**: Content-based heuristic detection (scanning for framework-specific keywords) — less reliable and duplicates adapter responsibility.

## Rule Pack Format

**Decision**: YAML files following the existing `ExtractionRule` schema with semver version metadata

**Rationale**: YAML is human-readable, matches the existing rule pack convention (IX. Rule Externalization), and allows customization without code changes. Semantic versioning (`major.minor.patch`) embedded in pack metadata provides compatibility tracking.

**Alternatives considered**: JSON schema (less readable), Python plugins (defeats externalization), unversioned files (no compatibility management).

## Rule Conflict Resolution

**Decision**: Priority-based (numeric 1–100), already implemented in `DeterministicSemanticEngine._load_rules()`

**Rationale**: Specialist rules are additive — they never override default rules. Priority ensures the correct execution order. Already implemented.

**Alternatives considered**: Override semantics (would violate additive-only constraint), last-writer-wins (non-deterministic).

## Performance Target

**Decision**: OpenSpec examples in `tests/openspec/` processed end-to-end in ≤ 30s

**Rationale**: The largest validation corpus (29 domains + 41 changes, ~70+ documents in `tests/openspec/`). A 30s target is practical for a deterministic regex-based pipeline without LLM overhead and provides a clear pass/fail bar for CI.

**Alternatives considered**: Per-document target (< 2s/doc) — harder to aggregate meaningfully; no target — cannot validate performance regressions.

## Observability

**Decision**: Per-document extraction success rate ≥ 99% as a counter metric, WARN on failures

**Rationale**: Provides operational visibility into extraction health without over-specifying implementation details. The existing debug output (match traces, unmatched statistics) covers development-time debugging.

**Alternatives considered**: Full structured JSON per document (too verbose for production), log-only (no metrics for alerting), no observability (cannot detect extraction degradation).

## Out of Scope

- LLM hybrid/assisted extraction mode — purely deterministic only
- User-defined/custom rule pack authoring — all packs are built-in and versioned with the codebase
- Cross-repository federation — single repository per run
- Real-time/interactive extraction — CLI batch mode only

## Key Dependencies

- `specmetrics` kernel: DeterministicSemanticEngine, ExtractionRule, EvidenceReference, CFM/CSM classifiers — all stable and available
- Framework adapters: SpeckitAdapter, OpenSpecAdapter — produce correct `document_type` metadata
- Test corpora: specmetrics itself (29 features) for Speckit; `tests/openspec/` (29 domains, 41 changes) for OpenSpec
