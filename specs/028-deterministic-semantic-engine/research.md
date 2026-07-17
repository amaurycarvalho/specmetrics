# Research Report: Deterministic Semantic Engine

**Date**: 2026-07-17 | **Feature**: [spec.md](spec.md)

---

## 1. Markdown AST Parser

**Decision**: Use `markdown-it-py` (existing constitution tech stack).

**Rationale**: Already in the project's approved technology stack. Produces a flat token stream with `Token.nesting` (+1 open, 0 self-closing, -1 close) that enables simple visitor traversal. Covers all token types required by FR-004: headings, lists, tables, paragraphs, code blocks, blockquotes, emphasis, and links.

**AST traversal strategy**: Visitors receive the full token list once and iterate sequentially, maintaining a heading hierarchy stack. Each visitor extracts observations for its token type into a shared `ExtractionState`.

**Alternatives considered**:
- **Regular expressions**: Explicitly rejected by RFC-031.
- **mistune**: Alternative parser but not in the tech stack.

---

## 2. Visitor Pattern Design

**Decision**: One dedicated visitor class per AST token type, all sharing a common `visit(tokens, state)` interface.

**Visitors**:
| Visitor | Token Types | Observations |
|---------|-------------|--------------|
| `HeadingVisitor` | `heading_open`, `heading_close`, `inline` | Heading text, level, hierarchy path, known section detection |
| `ListVisitor` | `bullet_list_open/close`, `ordered_list_open/close`, `list_item_open/close` | List items with nesting level |
| `TableVisitor` | `table_open/close`, `thead_open/close`, `tbody_open/close`, `tr_open/close`, `th_open/close`, `td_open/close` | Table rows, headers, cell content |
| `ParagraphVisitor` | `paragraph_open/close` | Paragraph text content |
| `CodeBlockVisitor` | `fence` | Code content, language tag |
| `QuoteVisitor` | `blockquote_open/close` | Blockquote content |
| `EmphasisVisitor` | `strong_open/close`, `em_open/close` | Bold/italic text spans |
| `LinkVisitor` | `link_open/close`, `inline` with link tokens | URLs, link text, reference links |

**Shared state**: `ExtractionState` dataclass with `heading_stack: list[str]`, `observations: list[Observation]`, `elements: list[ExtractedElement]`.

**Alternatives considered**:
- **Single monolithic visitor**: Violates SRP, harder to test and extend.

---

## 3. Rule Engine Architecture

**Decision**: Two-phase rule engine: (1) visitors produce `Observation` objects → (2) rule engine matches observations against loaded rules to produce `ExtractedElement`.

**Rule format** (YAML):
```yaml
rules:
  - id: "user-story"
    name: "User Story"
    pattern:
      keywords: ["As a", "I want", "So that"]
      min_matches: 2
    type: "entity"
    confidence: 0.95
    priority: 80

  - id: "gwt"
    name: "Given/When/Then"
    pattern:
      keywords: ["Given", "When", "Then"]
      min_matches: 2
    type: "fact"
    confidence: 0.85
    priority: 70

  - id: "requirement-shall"
    name: "Requirement Statement"
    pattern:
      keywords: ["Must", "Shall", "Should", "Will"]
      min_matches: 1
    type: "fact"
    confidence: 0.70
    priority: 60

  - id: "business-rule"
    name: "Business Rule"
    pattern:
      keywords: ["If", "Then"]
      min_matches: 2
    type: "fact"
    confidence: 0.70
    priority: 60

  - id: "actors-section"
    name: "Actors Section"
    pattern:
      heading: "Actors"
    type: "entity"
    confidence: 1.00
    priority: 90

  - id: "constraints-section"
    name: "Constraints Section"
    pattern:
      heading: "Constraints"
    type: "entity"
    confidence: 1.00
    priority: 90

  - id: "assumptions-section"
    name: "Assumptions Section"
    pattern:
      heading: "Assumptions"
    type: "entity"
    confidence: 1.00
    priority: 90

  - id: "decisions-section"
    name: "Decisions Section"
    pattern:
      heading: "Decisions"
    type: "entity"
    confidence: 1.00
    priority: 90

  - id: "glossary-section"
    name: "Glossary Terms"
    pattern:
      heading: "Glossary" | "Glossary Terms"
    type: "entity"
    confidence: 1.00
    priority: 90
```

**Alternatives considered**:
- **Hardcoded pattern matchers in visitor code**: Violates Rule Externalization (Principle IX).
- **DSL for rules**: Over-engineered for v1; YAML with structured fields is sufficient.

---

## 4. Rule Pack Loading

**Decision**: `RulePackLoader` class that reads YAML files, validates required fields, and returns `list[ExtractionRule]`.

**Loading order**: Built-in `default_rule_pack.yaml` loaded first, then any additional packs from `extra_rule_packs` config. Rules merged into single list; conflicts resolved by priority score (higher wins).

**Validation**: Each rule must have non-empty `id`, `name`, `pattern`, valid `type` (one of `fact`, `entity`, `relationship`, `operation`), `confidence` in 0.0–1.0, and `priority` in 1–100. Invalid rules are skipped with logged warning.

**Alternatives considered**:
- **TOML or JSON rule packs**: YAML is already in the project tech stack (ruamel.yaml).

---

## 5. Engine Configuration

**Decision**: DeterministicSemanticEngine accepts a configuration dict with the following keys:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `max_heading_depth` | `int` | `6` | Maximum heading depth to process; deeper headings flattened |
| `default_rule_pack` | `str \| Path` | built-in | Path to default rule pack YAML |
| `extra_rule_packs` | `list[str \| Path]` | `[]` | Additional rule pack paths |
| `default_confidence` | `float` | `0.70` | Confidence for pattern-inferred elements |

**Alternatives considered**:
- **Pydantic Settings model**: Over-engineered for a kernel-internal engine. Dict is consistent with F27 engine config pattern.

---

## 6. Evidence Reference with Extraction Rule

**Decision** (per FR-008 clarification): Each `EvidenceReference` includes an additional `rule_id` field identifying which rule produced the element, beyond the standard F27 fields (`document_id`, `section_id`, `text`).

This is an extension of the F27 canonical model specific to the deterministic engine. The downstream Evidence Graph layer receives the same schema regardless.

---

## 7. Framework-Aware Rules (OpenSpec, SpecKit)

**Decision**: Framework-specific rules (OpenSpec, SpecKit) are shipped as separate rule pack YAML files in the `rules/` directory. They are loaded as extra packs when the corresponding framework document type is detected.

**Framework detection**: The engine checks document metadata (`document_type` field from F03) to determine which framework packs to activate.

**Alternatives considered**:
- **Hardcoded framework logic in visitors**: Violates Rule Externalization.
- **Single monolithic rule pack**: Makes it harder to evolve framework support independently.
