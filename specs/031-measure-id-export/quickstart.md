# Quickstart Validation Guide: Measure ID & Export Commands

## Prerequisites

- SpecMetrics installed (`pipx install specmetrics` or `uv tool install specmetrics`)
- A project with an SDD framework (OpenSpec or SpecKit)
- Working directory set to the project root

## Validation Scenarios

### Scenario 1: Basic Measure Run with ID

**Setup**: Ensure `.specmetrics/runs/` does not exist (or note current state).

**Command**:
```bash
specmetrics measure
```

**Expected outcome**:
1. Output includes `Measure ID: <id>` where `<id>` matches `YYYYMMDD-HHMMSS-<8-char-hex>`
2. `.specmetrics/runs/<id>/` directory is created
3. `.specmetrics/runs/<id>/` contains at minimum `metadata.json` and stage JSON files
4. `.specmetrics/output/specmetrics-output.json` contains `measure.id` and `measure.id_path` fields before `measure.sdd_framework`

**Validation commands**:
```bash
# Check run directory exists
ls .specmetrics/runs/
# Check contents
cat .specmetrics/runs/*/metadata.json | python3 -m json.tool
# Check specmetrics-output.json has new fields
python3 -c "import json; d=json.load(open('.specmetrics/output/specmetrics-output.json')); print('id:', d['measure'].get('id')); print('id_path:', d['measure'].get('id_path'))"
```

---

### Scenario 2: Measure with `--export` Flag

**Setup**: Run `specmetrics measure` first to have a valid project state.

**Command**:
```bash
specmetrics measure --export
```

**Expected outcome**:
1. Measure ID printed
2. Run directory created in `.specmetrics/runs/`
3. Export files created in `exports/` (default JSON format)
4. `exports/discover.json`, `exports/measure.json`, etc. exist with valid JSON content

**Validation commands**:
```bash
ls exports/
python3 -c "import json; d=json.load(open('exports/discover.json')); print('stage:', d['name'], 'entities:', len(d.get('entities', [])))"
```

---

### Scenario 3: Measure with `--export --format csv`

**Command**:
```bash
specmetrics measure --export --format csv
```

**Expected outcome**:
1. Measure ID printed
2. Run directory created
3. CSV files in `exports/` (e.g., `exports/discover.csv`, `exports/measure.csv`)
4. CSV files are valid and have headers matching stage content

**Validation commands**:
```bash
head -5 exports/discover.csv
python3 -c "import csv; r=csv.DictReader(open('exports/discover.csv')); print('cols:', r.fieldnames)"
```

---

### Scenario 4: List Available Runs

**Setup**: Run `specmetrics measure` two or more times.

**Command**:
```bash
specmetrics export list
```

**Expected outcome**:
1. All measure IDs displayed in table format
2. Ordered most recent first
3. Each row shows ID and creation timestamp

**Validation commands**:
```bash
specmetrics export list
# Verify count matches
ls -d .specmetrics/runs/*/ | wc -l
```

---

### Scenario 5: Export Specific Run

**Setup**: Note a measure ID from a previous run.

**Command**:
```bash
specmetrics export run <measure-id>
```

**Expected outcome**:
1. Files created in `exports/` (overwriting previous content)
2. JSON files byte-identical to source in `.specmetrics/runs/<measure-id>/`

**Validation commands**:
```bash
diff <(cat .specmetrics/runs/<measure-id>/discover.json) <(cat exports/discover.json)
```

---

### Scenario 6: Export Latest Run (Default)

**Command**:
```bash
specmetrics export run
```

**Expected outcome**:
1. Uses the most recent run directory
2. Same output as explicitly specifying that ID

---

### Scenario 7: Export with Nonexistent ID

**Command**:
```bash
specmetrics export run nonexistent-id-12345
```

**Expected outcome**:
1. Error message: `Measure run "nonexistent-id-12345" not found.`
2. Exit code 1

---

### Scenario 8: Export with No Runs (Backward Compatibility)

**Setup**: Remove or rename `.specmetrics/runs/` so no runs exist.

**Command**:
```bash
specmetrics export run
```

**Expected outcome**:
1. Falls back to running the measurement pipeline directly
2. Export files generated in `exports/` from fresh pipeline execution
3. No error message about missing runs

---

### Scenario 9: JSON Output Includes `measure.id` and `measure.id_path`

**Setup**: After `specmetrics measure`.

**Command**:
```bash
python3 -c "
import json
d = json.load(open('.specmetrics/output/specmetrics-output.json'))
order = list(d['measure'].keys())
id_idx = order.index('id')
sdd_idx = order.index('sdd_framework')
print(f'id before sdd_framework: {id_idx < sdd_idx}')
print(f'id_path: {d[\"measure\"].get(\"id_path\")}')
"
```

**Expected outcome**:
- `id_idx < sdd_idx` is `True`
- `id_path` matches the last component of the run directory path

---

## Expected Test Results

| Scenario | Test | Expected Exit Code |
|----------|------|--------------------|
| 1 | Basic measure | 0 |
| 2 | Measure + export (JSON) | 0 |
| 3 | Measure + export (CSV) | 0 |
| 4 | List runs | 0 |
| 5 | Export specific run | 0 |
| 6 | Export latest run | 0 |
| 7 | Export nonexistent ID | 1 |
| 8 | Export with no runs (fallback) | 0 |
| 9 | JSON field ordering | 0 |
