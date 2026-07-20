# Quickstart: Populate Stage Entities on Run Artifacts

## Prerequisites

- Python 3.13+ with `uv`
- SpecMetrics installed in development mode: `uv pip install -e .`
- A project with specification files (e.g., the specmetrics repo itself, which uses `speckit`)

## Setup

No additional setup required. The feature modifies the run artifact serialization path, which triggers on every `specmetrics measure` invocation.

## Validation Scenarios

### Scenario 1: Basic entity population

Run `specmetrics measure` on the specmetrics project itself, which contains its own `.sdd` specification files:

```bash
specmetrics measure --stage discover
```

**Expected outcome**: `~/.specmetrics/runs/<id>/discover.json` contains:
- `entities` is non-empty (list of discovered documents)
- Each entity has `id`, `document_type`, and `path`
- `count` matches `entities.length`

### Scenario 2: All stages populated

```bash
specmetrics measure
```

**Expected outcome**: All 8 stage files in `.specmetrics/runs/<id>/` have populated `entities`:
- `discover.json` → document entries
- `extract.json` → extracted element entries
- `graph.json` → node entries + summary
- `csm.json` → categorized CSM entities
- `cfm.json` → categorized CFM entities
- `rule.json` → applied rule pack entries
- `measure.json` → metric results with breakdowns
- `export.json` → exported file paths

### Scenario 3: Truncation with configurable limit

Create a `.specmetrics/config.yml` (or `specmetrics.yml` in project root):

```yaml
run_artifacts:
  max_entities_per_stage: 100
```

```bash
specmetrics measure
```

**Expected outcome**: Stage files with more than 100 entities contain `_truncated: true` and `_total_count` showing the actual total. `entities` list has exactly 100 entries.

### Scenario 4: Backward compatibility

Run `specmetrics measure` and verify the top-level keys for each stage file match the previous format:

```bash
python3 -c "
import json
for stage in ['discover','extract','graph','csm','cfm','rule','measure','export']:
    path = list(Path('.specmetrics/runs').glob('*/*.json'))  # find latest
"
```

**Expected outcome**: Each file still has `name`, `count`, `count_type`, `duration_ms`, and `entities` — same shape as before, just `entities` now contains data.

### Scenario 5: Skipped stage handling

```bash
specmetrics measure --from measure
```

**Expected outcome**: Stage files for discover, extract, graph, csm, cfm, rule each have `count: 0` and `entities: []`.

## Verification Script

```python
#!/usr/bin/env python3
"""Verify stage artifacts have populated entities."""
import json
from pathlib import Path

runs_dir = Path(".specmetrics/runs")
run_dirs = sorted(runs_dir.iterdir())
if not run_dirs:
    print("No runs found. Run 'specmetrics measure' first.")
    exit(1)

latest = run_dirs[-1]
all_populated = True
for stage_file in latest.glob("*.json"):
    if stage_file.name == "metadata.json":
        continue
    data = json.loads(stage_file.read_text())
    entry = data[0]
    has_entities = len(entry.get("entities", [])) > 0
    status = "✓" if has_entities else "✗"
    name = entry["name"]
    count = entry["count"]
    entity_count = len(entry["entities"])
    print(f"  {status} {name}: count={count}, entities={entity_count}")
    if not has_entities:
        all_populated = False

if all_populated:
    print("\nAll stages have populated entities.")
else:
    print("\nSome stages have empty entities.")
    exit(1)
```

Run with:

```bash
python3 verify_entities.py
```

## Related Documents

- [Data Model](data-model.md) — per-stage entity schemas
- [Contract: Stage Artifact Schema](contracts/stage-artifact-schema.md) — JSON validation rules
- [Spec](spec.md) — feature requirements and success criteria
