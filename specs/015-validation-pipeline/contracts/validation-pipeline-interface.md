# Validation Pipeline Contracts

## CLI Interface

### Command: `specmetrics validate`

```
Usage: specmetrics validate [OPTIONS] SPEC_PATH...

Arguments:
  SPEC_PATH...  Path(s) to specification file(s) or directory(ies)  [required]

Options:
  --rules PATH          Path to custom validation rules configuration
  --format TEXT         Output format: text (default), json, quiet
  --batch               Treat paths as a batch (default when multiple paths given)
  --constitution-only   Only run constitutional compliance checks
  --structural-only     Only run structural checks
  --help                Show this message and exit
```

**Exit codes**:
- `0` — All validation checks passed
- `1` — One or more validation checks failed
- `2` — Invalid arguments or configuration error

### JSON Output Format

When `--format json` is specified, output is written to stdout as JSON:

```json
{
  "version": "1.0",
  "overall_passed": false,
  "documents": [
    {
      "path": "specs/015-validation-pipeline/spec.md",
      "passed": true,
      "duration_ms": 320,
      "results": [
        {
          "rule": "mandatory-sections-exist",
          "passed": true,
          "message": "All mandatory sections present",
          "evidence": [
            {
              "section": "User Scenarios & Testing",
              "line": 11,
              "detail": "Section heading found at line 11"
            }
          ]
        }
      ],
      "summary": {
        "total": 7,
        "passed": 7,
        "failed": 0,
        "warnings": 0
      }
    }
  ],
  "summary": {
    "total_documents": 1,
    "passed_documents": 1,
    "failed_documents": 0,
    "total_rules": 7,
    "total_passed": 7,
    "total_failed": 0,
    "duration_ms": 320
  }
}
```

## Python API

### ValidationPipeline

```python
class ValidationPipeline:
    def run(self, document: SpecificationDocument) -> ValidationReport: ...
    def run_batch(self, documents: list[SpecificationDocument]) -> BatchReport: ...
    def load_rules(self, config_path: Path | None = None) -> list[ValidationRule]: ...
```

### ValidationRule Protocol (Plugin Interface)

Plugins implement validation rules via a callable protocol:

```python
class ValidationRule:
    name: str
    description: str
    category: RuleCategory
    severity: RuleSeverity

    def validate(self, document: SpecificationDocument) -> ValidationResult: ...
```

Entry point group: `specmetrics.validation_rules`

## Configuration

### Rule Configuration File (YAML)

```yaml
# .specmetrics/rules/validation-rules.yml
rules:
  mandatory-sections-exist:
    enabled: true
    sections:
      - "User Scenarios & Testing"
      - "Constitution Check"
      - "Requirements"
      - "Success Criteria"
      - "Assumptions"

  constitution-engaged:
    enabled: true

  file-not-empty:
    enabled: true
```
