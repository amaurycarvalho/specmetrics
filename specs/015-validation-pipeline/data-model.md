# Data Model: Validation Pipeline

## Entities

### SpecificationDocument

Represents a specification file being validated.

| Field | Type | Description |
|---|---|---|
| `path` | Path | File path to the spec document |
| `content` | str | Raw text content of the document |
| `format` | str | Document format (e.g., "spec-markdown") |
| `size_bytes` | int | File size in bytes |
| `line_count` | int | Number of lines in the document |

**Relationships**: Input to the ValidationPipeline. One SpecificationDocument produces one ValidationReport.

### ValidationRule

A single check to be performed against a specification document.

| Field | Type | Description |
|---|---|---|
| `name` | str | Unique rule identifier (e.g., "mandatory-sections-exist") |
| `description` | str | Human-readable description of what the rule validates |
| `category` | RuleCategory | Classification: STRUCTURAL, CONSTITUTIONAL, FORMAT |
| `severity` | RuleSeverity | Error or Warning |
| `enabled` | bool | Whether the rule is active |

**Relationships**: Applied by the ValidationPipeline. Each rule produces zero or more ValidationResults per document.

**Categories**:
- STRUCTURAL: Mandatory section presence, template format compliance
- CONSTITUTIONAL: Constitution principle engagement, compliance note requirements
- FORMAT: Document encoding, file validity, parseability

### ValidationResult

The outcome of applying a single ValidationRule to a SpecificationDocument.

| Field | Type | Description |
|---|---|---|
| `rule_name` | str | Name of the rule that produced this result |
| `passed` | bool | True if the spec satisfies the rule |
| `evidence` | list[EvidenceRef] | References to spec sections/text that justify the result |
| `message` | str | Human-readable description of what was checked and the outcome |
| `severity` | RuleSeverity | Inherited from the rule |

**Relationships**: Belongs to a ValidationReport. References section-level evidence in the spec document.

### ValidationReport

The aggregate result of validating a single SpecificationDocument.

| Field | Type | Description |
|---|---|---|
| `document_path` | Path | Path to the validated spec |
| `overall_passed` | bool | True only if all rules passed |
| `results` | list[ValidationResult] | Per-rule validation outcomes |
| `summary` | ReportSummary | Counts of passed/failed/warning results |

**Relationships**: Produced by the ValidationPipeline for one document. Contains multiple ValidationResults.

### ReportSummary

Aggregated counts for a validation run.

| Field | Type | Description |
|---|---|---|
| `total_rules` | int | Number of rules executed |
| `passed` | int | Number of passing rules |
| `failed` | int | Number of failing rules |
| `warnings` | int | Number of warnings |
| `duration_ms` | int | Time taken to run all rules |

### BatchReport

Summary of validating multiple SpecificationDocuments.

| Field | Type | Description |
|---|---|---|
| `reports` | list[ValidationReport] | Per-document reports |
| `total_documents` | int | Total documents validated |
| `passed_documents` | int | Documents where all rules passed |
| `failed_documents` | int | Documents with at least one failing rule |
| `duration_ms` | int | Total batch duration |

## State Transitions

```text
SpecificationDocument (file path)
        │
        ▼
ValidationPipeline.run(document)
        │
        ├──► Load rules (from plugins / config)
        │
        ├──► Parse document (markdown-it-py)
        │
        ├──► For each rule:
        │       └──► Apply rule → ValidationResult
        │
        └──► Aggregate → ValidationReport
```

Batch flow extends the above:

```text
List[SpecificationDocument]
        │
        ▼
For each document ──► ValidationPipeline.run(document)
        │
        ▼
Aggregate → BatchReport
```

## Validation Rules (Built-in)

| Rule Name | Category | Description |
|---|---|---|
| `file-readable` | FORMAT | Document file exists, is readable, and has valid encoding |
| `file-not-empty` | FORMAT | Document content is not empty |
| `parseable-markdown` | FORMAT | Document can be parsed as markdown |
| `mandatory-sections-exist` | STRUCTURAL | All required template sections are present |
| `no-unknown-sections` | STRUCTURAL | No unrecognized section headings |
| `constitution-engaged` | CONSTITUTIONAL | Engaged principles are listed and addressed |
| `constitution-compliance-notes` | CONSTITUTIONAL | Compliance notes explain how each principle is satisfied |
