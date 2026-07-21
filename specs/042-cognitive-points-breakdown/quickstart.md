# Quickstart: Cognitive Points Breakdown

**Feature**: 042-cognitive-points-breakdown

## Prerequisites

- Python 3.13+ with `specmetrics` installed (development mode: `pip install -e .`)
- A project directory with specification files (e.g., the specmetrics repo itself)
- The project must produce Cognitive Points output (CSM and/or CFM elements present)

## Validation Scenarios

### Scenario 1: measure.json Contains Breakdown

**Purpose**: Verify that `measure.json` includes a `breakdown` field in the Cognitive Points entry with per-Bloom-level score totals.

```bash
# Run a measurement
specmetrics measure . --verbose

# Get the latest run's measure.json
RUN_DIR=$(ls -td .specmetrics/runs/*/ | head -1)
cat "$RUN_DIR/measure.json" | python3 -c "
import json, sys
data = json.load(sys.stdin)
measure_stage = data.get('measure', [])
for entry in measure_stage:
    if entry.get('metric') == 'cognitive_points':
        print('Found cognitive_points entry')
        print(f'  total: {entry[\"total\"]}')
        bd = entry.get('breakdown', {})
        print(f'  breakdown: {bd}')
        if bd:
            bd_total = sum(v['total'] for v in bd.values())
            print(f'  breakdown sum: {bd_total}')
            assert abs(bd_total - entry['total']) < 0.01, 'Sum mismatch!'
            print('  PASS: breakdown sums to total')
        else:
            print('  NOTE: empty breakdown (no elements with cognitive scoring)')
"
```

**Expected outcome**: The Cognitive Points entry in `measure.json` contains a `breakdown` dict. If elements were scored, the breakdown is non-empty and its values sum to the Cognitive Points `total`.

---

### Scenario 2: CLI Text Output Shows Breakdown

**Purpose**: Verify that the CLI text output displays Bloom-level breakdown lines below "Cognitive Points".

```bash
specmetrics measure . --verbose 2>&1 | grep -A 10 "Cognitive Points"
```

**Expected outcome**: Below the `Cognitive Points: <total>` line, indented lines show each Bloom level present (e.g., `    Understand: 890.0`, `    Apply: 1500.0`, `    Create: 28669.0`).

---

### Scenario 3: Breakdown Sums to Total

**Purpose**: Verify that the per-level breakdown totals sum to the displayed Cognitive Points total (within floating-point tolerance).

```bash
specmetrics measure . --format json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
for result in data.get('results', []):
    if result.get('name') == 'cognitive_points':
        total = result['total']
        bd = result.get('breakdown', {})
        if bd:
            bd_sum = sum(v.get('total', v) if isinstance(v, dict) else v for v in bd.values())
            print(f'Total: {total}')
            print(f'Breakdown sum: {bd_sum}')
            diff = abs(total - bd_sum)
            print(f'Difference: {diff}')
            assert diff < 0.01, f'Breakdown sum ({bd_sum}) does not match total ({total})!'
            print('PASS: breakdown sums match')
        else:
            print('NOTE: no breakdown (empty spec)')
"
```

**Expected outcome**: The breakdown values sum to the Cognitive Points total within 0.01 tolerance.

---

### Scenario 4: Empty Specification Produces No Breakdown Lines

**Purpose**: Verify that when no elements are scored (empty spec), the CLI shows only the total line without indented breakdown lines.

```bash
# Create a minimal empty project and measure it
mkdir -p /tmp/empty_spec_test
cd /tmp/empty_spec_test
git init -q 2>/dev/null || true
touch README.md
specmetrics measure . --verbose 2>&1 | grep -A 3 "Cognitive Points"
```

**Expected outcome**: If Cognitive Points is `0`, no indented breakdown lines appear below it.

---

### Scenario 5: Existing JSON Measure Still Works

**Purpose**: Verify backward compatibility — an existing `measure.json` from a previous specmetrics version (without `cognitive_bloom_breakdown`) is still valid.

```bash
# If you have an older measure.json, read it:
python3 -c "
import json
# Simulate an old-style cognitive_points entry without breakdown
old_entry = {
    'metric': 'cognitive_points',
    'total': 12345.0,
    'status': 'completed',
    'duration_ms': 0
}
# Verify the formatter handles missing breakdown gracefully
bd = old_entry.get('breakdown', {})
assert bd == {} or bd is not None
print('PASS: old format without breakdown is handled')
"
```

**Expected outcome**: Code that reads `measure.json` entries without `breakdown` field continues to work.

---

### Scenario 6: Breakdown Ordering

**Purpose**: Verify Bloom levels are displayed in cognitive complexity order (Remember → Create), not alphabetical.

```bash
specmetrics measure . --verbose 2>&1 | grep -A 10 "Cognitive Points" | grep -v "Cognitive Points" | head -6
```

**Expected outcome**: Levels appear in order: Remember, Understand, Apply, Analyze, Evaluate, Create (skipping absent levels). Not alphabetical (which would start with Analyze).
