# Quickstart: Eliminate Surviving Mutants

**Feature**: 046-survivor-mutant-tests | **Date**: 2026-08-10

## Prerequisites

- Python 3.13 environment with project dependencies installed (`uv sync` or equivalent)
- `mutants/mutmut-cicd-results.log` present at repository root
- `pytest` and `ruff` available in PATH
- Working directory: repository root

## Execution Overview

The workflow is executed as an AI-assisted sequential process. No new CLI tool is built; the AI agent performs each step directly.

### Phase 1: Parse & Group

**Input**: `mutants/mutmut-cicd-results.log`
**Output**: In-memory grouped survivor list by module

**Validation**: Survivor count from log matches parsed count (8,822).

### Phase 2: Guard Analysis

**Input**: Grouped survivor list
**Output**: Classification for each survivor

**For each survivor**, step-by-step:
1. Extract source file path, line number, and mutation diff from the survivor entry
2. Locate the corresponding test file at `tests/<mirror-path>/test_<module>.py`
3. Search the test file for test functions that:
   - Import or reference the mutated function
   - Assert on the exact behavior the mutation alters
4. Classify: `ALREADY_GUARDED` if a test covers the mutated behavior; `EQUIVALENT` if a heuristic rule matches; otherwise `NEEDS_NEW_TEST`

### Phase 3: Test Generation

**Input**: Survivors classified as `NEEDS_NEW_TEST`
**Output**: Test functions added to test files

**For each unguarded survivor**, step-by-step:
1. Read the mutated source line and surrounding context
2. Determine the behavior change the mutation introduces
3. Write a pytest function that:
   - Import the function/class under test
   - Sets up the exact inputs that trigger the mutated code path
   - Asserts on the output/side-effect the mutation would alter
   - Contains a docstring referencing the mutation ID
4. Append the test to the appropriate test file (or create the file if needed)

### Phase 4: Individual Validation

**For each modified/created test**:
```bash
pytest tests/<path>/test_<module>.py::<test_function_name>
```
Expected: test passes (exit code 0).

If a test fails, fix it and re-run before moving to the next.

### Phase 5: Lint & Full Suite

```bash
ruff check .
```
Expected: zero new findings.

```bash
pytest tests/
```
Expected: all tests pass (exit code 0).

If either fails, fix failures and re-run until both pass.

### Phase 6: Report Generation

Write `mutants/survivor-analysis.md` with:
- Summary table (total, guarded, new-test, equivalent, skipped counts)
- Per-module sections with survivor tables
- Equivalent mutants section for human review
- List of files modified

## Verification Checklist

After completion, verify:

- [ ] `mutants/survivor-analysis.md` exists and contains all 8,822 survivors classified
- [ ] Every `NEEDS_NEW_TEST` survivor has a corresponding test function
- [ ] `ruff check .` passes with zero new findings
- [ ] `pytest tests/` passes with all tests green
- [ ] No `mutmut` command was executed (check shell history)
- [ ] All new tests follow the existing project test conventions
- [ ] No source files outside `tests/` were modified

## Expected Outcomes

| Metric | Target |
|--------|--------|
| Survivors classified | 8,822 / 8,822 |
| New tests added | Depends on guard coverage (expected: majority) |
| Tests passing individually | 100% |
| Lint passing | Zero new findings |
| Full suite passing | 100% |
| Mutation score improvement | To be verified by user running `mutmut` manually |
