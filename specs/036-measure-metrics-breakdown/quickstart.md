# Quickstart: Measure Metrics Breakdown

**Feature**: 036-measure-metrics-breakdown

## Prerequisites

- Python 3.13+ with `specmetrics` installed (development mode: `pip install -e .`)
- A project directory with specification files (SpecKit or OpenSpec format)
- At least one functional process defined in the specifications

## Validation Scenarios

### Scenario 1: metrics.json Generated with All Metrics

**Purpose**: Verify `metrics.json` is created alongside existing artifacts with all 8 metrics enabled.

```bash
# Run measurement on a project
specmetrics measure /path/to/spec-project --metrics all

# Check the run directory
ls .specmetrics/runs/<measure_id>/

# Expected files:
# metadata.json  discover.json  extract.json  graph.json  csm.json  cfm.json
# rule.json  measure.json  export.json  metrics.json  <-- NEW
```

**Verification**:
```bash
# Check metrics.json exists and is valid JSON
python3 -c "
import json
with open('.specmetrics/runs/<measure_id>/metrics.json') as f:
    data = json.load(f)
print(f'Metrics: {[m[\"name\"] for m in data]}')
print(f'Statuses: {[m[\"status\"] for m in data]}')
"
```

**Expected outcome**: Output lists metric names (`fpa`, `sfp`, `snap`, `bcp`, `sp`, `tshirt`, `tp`, `cp`) with status `"success"` for each.

### Scenario 2: Filtered Metrics

**Purpose**: Verify only selected metrics appear in `metrics.json`.

```bash
specmetrics measure /path/to/spec-project --metrics fpa,sp
```

**Verification**:
```bash
python3 -c "
import json
with open('.specmetrics/runs/<measure_id>/metrics.json') as f:
    data = json.load(f)
names = {m['name'] for m in data}
assert names == {'fpa', 'sp'}, f'Expected fpa+sp, got {names}'
print('PASS: Only selected metrics present')
"
```

### Scenario 3: Uniform Schema Verification

**Purpose**: Verify all metric entries share the same top-level keys and all entities share the same keys.

```bash
python3 -c "
import json

with open('.specmetrics/runs/<measure_id>/metrics.json') as f:
    data = json.load(f)

METRIC_KEYS = {'name', 'metric', 'total', 'unit', 'entity_count', 'entities', 'status'}
ENTITY_KEYS = {'id', 'name', 'type', 'score'}

CANONICAL_TYPES = {
    'data_group', 'operation', 'functional_process', 'specification_activity',
    'business_rule', 'actor', 'relationship', 'decision', 'assumption',
    'constraint', 'risk', 'open_question', 'acceptance_criteria', 'glossary_term'
}

for entry in data:
    missing = METRIC_KEYS - set(entry.keys())
    assert not missing, f'{entry[\"name\"]} missing keys: {missing}'

    assert entry['entity_count'] == len(entry['entities']), \
        f'{entry[\"name\"]}: entity_count mismatch'

    for entity in entry['entities']:
        missing_e = ENTITY_KEYS - set(entity.keys())
        assert not missing_e, f'Entity {entity[\"id\"]} missing keys: {missing_e}'
        assert entity['type'] in CANONICAL_TYPES, \
            f'Entity {entity[\"id\"]} has unknown type: {entity[\"type\"]}'

    print(f'{entry[\"name\"]}: {entry[\"entity_count\"]} entities, total={entry[\"total\"]} {entry[\"unit\"]}')
print('PASS: Uniform schema verified')
"
```

### Scenario 4: Entity ID Format

**Purpose**: Verify all entity IDs follow the compound URI format.

```bash
python3 -c "
import json, re
pattern = re.compile(r'^(cfm|csm):[a-z_]+:.+$')

with open('.specmetrics/runs/<measure_id>/metrics.json') as f:
    data = json.load(f)

bad = []
for entry in data:
    for entity in entry['entities']:
        if not pattern.match(entity['id']):
            bad.append(entity['id'])

assert not bad, f'Bad ID format: {bad}'
print(f'PASS: All {sum(e[\"entity_count\"] for e in data)} entity IDs valid')
"
```

### Scenario 5: Score Matches Total

**Purpose**: Verify that for successful metrics, the sum of entity scores equals the metric total.

```bash
python3 -c "
import json

with open('.specmetrics/runs/<measure_id>/metrics.json') as f:
    data = json.load(f)

for entry in data:
    if entry['status'] == 'success':
        computed = sum(e['score'] for e in entry['entities'])
        delta = abs(computed - entry['total'])
        assert delta < 0.01, \
            f'{entry[\"name\"]}: total={entry[\"total\"]}, sum of entities={computed}'
        print(f'{entry[\"name\"]}: total={entry[\"total\"]} == sum of {entry[\"entity_count\"]} entities ✓')
print('PASS: All totals match entity sums')
"
```

### Scenario 6: FPA Entity Metadata

**Purpose**: Verify FPA entities carry their complexity classification in metadata.

```bash
python3 -c "
import json

with open('.specmetrics/runs/<measure_id>/metrics.json') as f:
    data = json.load(f)

fpa = next(m for m in data if m['name'] == 'fpa')
assert fpa['metadata']['method'] == 'ifpug'

for e in fpa['entities']:
    assert 'function_type' in e['metadata'], f'{e[\"id\"]} missing function_type'
    assert 'complexity' in e['metadata'], f'{e[\"id\"]} missing complexity'
    assert e['metadata']['function_type'] in ('ILF', 'EIF', 'EI', 'EO', 'EQ')
    assert e['type'] in ('data_group', 'operation')

print(f'PASS: FPA metadata verified for {fpa[\"entity_count\"]} entities')
"
```

### Scenario 7: Integration with Existing Artifacts

**Purpose**: Verify no existing files are broken by the addition of `metrics.json`.

```bash
# Check that metadata.json still exists and is valid
python3 -c "
import json
with open('.specmetrics/runs/<measure_id>/metadata.json') as f:
    meta = json.load(f)
assert 'id' in meta
print(f'metadata.json OK: id={meta[\"id\"]}')
"

# Check that measure.json still exists
test -f ".specmetrics/runs/<measure_id>/measure.json" && echo "measure.json OK"

# Check export doesn't break
specmetrics list runs
```

### Scenario 8: Empty Project / No Entities

**Purpose**: Verify metrics with zero entities produce valid empty entries.

```bash
# Run on an empty project (no functional processes)
specmetrics measure /path/to/empty-project --metrics fpa

python3 -c "
import json
with open('.specmetrics/runs/<measure_id>/metrics.json') as f:
    data = json.load(f)

fpa = data[0]
assert fpa['entity_count'] == 0
assert fpa['total'] == 0
assert fpa['entities'] == []
assert fpa['status'] == 'success'
print('PASS: Empty project handled correctly')
"
```

## Known Limitations

- Entity `metadata` fields vary by metric; consumers should check for key presence before accessing
- Entity `id` format is a compound URI but uniqueness within a run is not enforced at the file level (relies on canonical model uniqueness)
- The `warnings` and `errors` arrays include messages from the measurement engines; format is not standardized across metrics
