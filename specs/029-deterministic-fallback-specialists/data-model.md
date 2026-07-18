# Data Model: Specialized Deterministic Fallbacks

## SpecialistRulePack

| Field | Type | Description |
|-------|------|-------------|
| `pack_id` | str | Unique identifier (e.g., `speckit`, `openspec`) |
| `version` | str | Semantic version string (`major.minor.patch`) |
| `rules` | list[ExtractionRule] | Ordered list of extraction rules |
| `document_types` | list[str] | Applicable document types (e.g., `specification`, `proposal`, `design`, `tasks`) |
| `framework` | str | Target framework identifier |
| `created` | date | Pack creation date |
| `description` | str | Human-readable description |

### Validation Rules

- `version` MUST follow semver format (`\d+.\d+.\d+`)
- Each `ExtractionRule` MUST have a unique `rule_id` within the pack
- `rules` MUST be ordered by descending priority (highest first)
- Major version mismatch against engine compatibility range MUST emit a warning on load

## ExtractionRule (from existing model, extended for specialists)

| Field | Type | Description |
|-------|------|-------------|
| `rule_id` | str | Unique rule identifier |
| `pattern` | str | Regex pattern for content matching |
| `semantic_type` | str | CFM semantic type (`entity`, `fact`, `operation`) |
| `confidence` | float | Confidence score (0.0–1.0) per FR-030 table |
| `priority` | int | Rule priority (1–100, higher = more specific) |
| `target_sections` | list[str] | Section headings to scope the rule to |
| `capture_groups` | dict | Named capture group mapping to semantic fields |
| `document_type` | str | Document type filter (optional) |

## EvidenceReference (existing model, populated by specialist rules)

| Field | Type | Description |
|-------|------|-------------|
| `document_id` | str | Source document identifier |
| `section_id` | str | Section heading within the document |
| `text_fragment` | str | Matched text content |
| `rule_id` | str | Originating extraction rule ID |

## ExtractionResult (per-document)

| Field | Type | Description |
|-------|------|-------------|
| `document_id` | str | Source document identifier |
| `elements` | list[ExtractedElement] | Extracted semantic elements |
| `rules_attempted` | int | Total rules executed |
| `rules_succeeded` | int | Rules that produced at least one match |
| `rules_failed` | int | Rules that threw an exception |
| `duration_ms` | int | Processing time for this document |
| `success_rate` | float | `rules_succeeded / rules_attempted` (target ≥ 99%) |

## Speckit and OpenSpec Domain Entities (for data group extraction)

### Speckit (from specmetrics analysis)

| Entity | Type | Description |
|--------|------|-------------|
| FeatureWorkspace | DataGroup | A single feature directory under `specs/###-name/` |
| SpecDocument | DataGroup | `spec.md` with User Stories, FRs, SCs, Key Entities |
| PlanDocument | DataGroup | `plan.md` with implementation plan |
| TasksDocument | DataGroup | `tasks.md` with implementation checklist |
| DataModelDocument | DataGroup | `data-model.md` with entity definitions |
| EvidenceReference | DataGroup | Provenance record per extracted element |

### OpenSpec (from tests/openspec/ examples)

| Entity | Type | Description |
|--------|------|-------------|
| TradeDay | DataGroup | Trading day entity |
| DominanceClassification | DataGroup | Dominance classifier output |
| Diagnosis | DataGroup | Market diagnosis entity |
| TickerList | DataGroup | List of stock tickers |
| CLVGauge | DataGroup | CLV gauge visualization |
| ClassificationBar | DataGroup | Classification bar chart |
| PriceRangeDiagram | DataGroup | Price range visualization |
| BuySellBar | DataGroup | Buy/sell indicator bar |
| B3Client | Actor | B3 API client |
| IndicatorEngine | Actor | Indicator computation engine |
| AnalyzeTickersUseCase | Actor | Use case for ticker analysis |
| FlowScopeGUI | Actor | GUI interface component |
| CacheManager | Actor | Cache management component |

## State Transitions

The deterministic extraction pipeline follows immutable, stateless transitions — no mutable state is maintained between documents:

```text
Document Loaded → Rule Pack Loaded → Rules Executed (per doc) → Elements Collected → Evidence References Attached → ExtractionResult Emitted
```

Each document is processed independently. Rule failures are caught and logged per-rule, never propagating to affect other documents or rules.
