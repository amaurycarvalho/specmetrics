# Data Model: Mutation Survivor Analysis

**Feature**: 046-survivor-mutant-tests | **Date**: 2026-08-10

## Entities

### MutationReport

The top-level container parsed from `mutants/mutmut-cicd-results.log`.

| Field | Type | Description |
|-------|------|-------------|
| killed | int | Count of killed mutants (11,888) |
| survived | int | Count of surviving mutants (8,822) |
| timeout | int | Count of timeout mutants (7) |
| suspicious | int | Count of suspicious mutants (0) |
| total | int | Total mutants evaluated (25,931) |
| score | float | Mutation score percentage (57.38%) |
| survivors | list[Survivor] | All surviving mutants |

### Survivor

A single surviving mutant entry from the report.

| Field | Type | Description |
|-------|------|-------------|
| mutation_id | str | Unique identifier (e.g., `mutmut_33`) |
| module_path | str | Fully-qualified module path (e.g., `specmetrics.plugins.rule_pack.validator`) |
| class_name | str | Class containing the mutation (from `xǁ` delimiter) |
| function_name | str | Function/method containing the mutation (from `xǁ` delimiter) |
| source_file | Path | Relative path to the source file (e.g., `specmetrics/plugins/rule_pack/validator.py`) |
| diff_hunk | str | The unified diff hunk (`@@ ... @@` section) |
| original_line | str | The original line content (prefixed with `-`) |
| mutated_line | str | The mutated line content (prefixed with `+`) |
| line_number | int | Line number in the source file where the mutation occurs |

### ModuleGroup

Survivors grouped by their source module prefix.

| Field | Type | Description |
|-------|------|-------------|
| module_name | str | Module grouping key (e.g., `specmetrics.plugins.rule_pack`) |
| source_files | list[Path] | Source files belonging to this module |
| survivors | list[Survivor] | Survivors in this module |
| test_files | list[Path] | Existing test files covering this module |

### GuardAnalysis

Result of analyzing a survivor against the existing test suite.

| Field | Type | Description |
|-------|------|-------------|
| survivor | Survivor | The survivor being analyzed |
| classification | Classification | `ALREADY_GUARDED`, `NEEDS_NEW_TEST`, `EQUIVALENT`, `SKIPPED` |
| rationale | str | Human-readable explanation of the classification |
| existing_test | str \| None | Name of the existing test that guards this survivor (if ALREADY_GUARDED) |
| equivalent_reason | str \| None | Heuristic rule that flagged this as equivalent (if EQUIVALENT) |
| equivalent_confidence | str \| None | `High`, `Medium`, or `Low` (if EQUIVALENT) |

### Classification

Enum of possible survivor classification outcomes.

| Value | Meaning |
|-------|---------|
| ALREADY_GUARDED | An existing test already asserts on the behavior the mutation alters |
| NEEDS_NEW_TEST | No existing test covers this behavior; a new test must be written |
| EQUIVALENT | The mutation is likely semantically equivalent; flagged for human review |
| SKIPPED | Survived for another reason (e.g., source file no longer exists, test infrastructure issue) |

### GeneratedTest

A test function written to kill a specific survivor.

| Field | Type | Description |
|-------|------|-------------|
| survivor | Survivor | The survivor this test targets |
| test_file | Path | Path to the test file where the test was added |
| test_function_name | str | Name of the generated test function |
| test_code | str | The test function source code |

### AnalysisReport

The final report written to `mutants/survivor-analysis.md`.

| Field | Type | Description |
|-------|------|-------------|
| generated_at | datetime | When the report was generated |
| summary | ReportSummary | Aggregate counts |
| module_sections | list[ModuleSection] | Per-module analysis sections |
| equivalent_section | list[Survivor] | Survivors flagged as equivalent |
| files_modified | list[Path] | Test files modified during the process |

### ReportSummary

| Field | Type | Description |
|-------|------|-------------|
| total_survivors | int | 8,822 |
| already_guarded | int | Count classified as ALREADY_GUARDED |
| needs_new_test | int | Count classified as NEEDS_NEW_TEST |
| equivalent | int | Count classified as EQUIVALENT |
| skipped | int | Count classified as SKIPPED |
| tests_added | int | Number of new test functions written |
| files_modified | int | Number of test files modified or created |

## Entity Relationships

```
MutationReport
  └── survivors: list[Survivor] (8,822 items)

ModuleGroup (derived by grouping Survivor.module_path prefix)
  └── survivors: list[Survivor]

GuardAnalysis (1:1 with Survivor)
  └── survivor: Survivor
  └── classification: Classification

GeneratedTest (1:1 with Survivor classified as NEEDS_NEW_TEST)
  └── survivor: Survivor

AnalysisReport (1:1 with MutationReport)
  └── summary: ReportSummary
  └── module_sections: list[ModuleSection]
  └── equivalent_section: list[Survivor]
```

## State Transitions

```
Survivor                      (parsed from log)
  │
  ▼
GuardAnalysis.pending         (not yet analyzed)
  │
  ├──► ALREADY_GUARDED        (existing test covers it → skip)
  ├──► EQUIVALENT             (heuristic flags it → document, skip)
  ├──► SKIPPED                (source missing, etc. → document, skip)
  └──► NEEDS_NEW_TEST         (not covered → write test)
         │
         ▼
       GeneratedTest           (test written)
         │
         ▼
       Test passed?            (individual run per FR-007)
         │
         ├──► YES → next survivor
         └──► NO  → fix test, re-run
```

## Validation Rules

- Survivor count in report summary MUST match count from `grep -c "^# " mutants/mutmut-cicd-results.log`
- Every survivor classified as NEEDS_NEW_TEST MUST have at least one GeneratedTest
- Every GeneratedTest MUST pass when run individually (`pytest <test_file>::<test_function>`)
- Equivalent confidence MUST be one of `High`, `Medium`, `Low`
- Files modified MUST NOT include any source file outside `tests/`
- The `mutmut` command MUST NOT appear in any executed command
