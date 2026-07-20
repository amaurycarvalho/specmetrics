# Quickstart: Clean Command for Runs Housekeeping

## Prerequisites

- SpecMetrics installed and working (`specmetrics --help` succeeds)
- A project directory with `.specmetrics/runs/` containing at least a few run folders (produced by `specmetrics measure`)
- Python 3.13+ with `pytest` installed (for validation tests)

## Validation Scenarios

### Scenario 1: Default behavior (keep last 90, keep 30 days)

**Setup**:
```bash
cd /path/to/specmetrics-project

# Create 100 simulated run folders (older than 30 days + recent)
# Using test helper or manual creation
```

**Run**:
```bash
specmetrics clean
```

**Expected outcome**: Only the 10 oldest runs (older than 30 days and outside the last 90) are deleted. Summary shows "Deleted 10 run(s). Kept 90 run(s)."

**Verification**:
```bash
ls .specmetrics/runs/ | wc -l
# Should show 90 remaining
```

---

### Scenario 2: Custom retention (keep 7 runs, keep 1 day)

**Run**:
```bash
specmetrics clean --keep-runs 7 --keep-days 1
```

**Expected outcome**: Only the most recent 7 runs from the last day are kept. All others are deleted.

---

### Scenario 3: Dry-run preview

**Run**:
```bash
specmetrics clean --dry-run
```

**Expected outcome**: Lists which runs would be deleted without actually deleting them. No files are removed.

**Verification**:
```bash
# Count runs before
ls .specmetrics/runs/ | wc -l

# Run dry-run
specmetrics clean --dry-run

# Count runs after (should be unchanged)
ls .specmetrics/runs/ | wc -l
```

---

### Scenario 4: Missing directory

**Run** (in a project without `.specmetrics/runs/`):
```bash
specmetrics clean
```

**Expected outcome**: Message "`.specmetrics/runs/` not found. Nothing to clean." Exit code 0.

---

### Scenario 5: Only run-count retention (no age limit)

**Run**:
```bash
specmetrics clean --keep-days 0 --keep-runs 50
```

**Expected outcome**: Keeps only the 50 most recent runs regardless of age. All older runs are deleted.

---

### Scenario 6: Only age-based retention (no run count limit)

**Run**:
```bash
specmetrics clean --keep-runs 0 --keep-days 7
```

**Expected outcome**: Keeps all runs from the last 7 days. Runs older than 7 days are deleted regardless of count.

---

### Scenario 7: Both thresholds disabled (delete everything)

**Run**:
```bash
specmetrics clean --keep-runs 0 --keep-days 0
```

**Expected outcome**: All run folders are deleted.

---

## Testing

### Unit Tests

```bash
pytest tests/unit/infrastructure/runs/test_cleaner.py -v
```

### CLI Integration Tests

```bash
pytest tests/cli/test_clean.py -v
```

## Contracts

Detailed CLI contract: [contracts/clean-cli.md](contracts/clean-cli.md)

## Data Model

Entity definitions: [data-model.md](data-model.md)
