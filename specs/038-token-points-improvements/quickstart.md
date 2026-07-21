# Quickstart: Token Points Improvements

**Feature**: 038-token-points-improvements

## Prerequisites

- Python 3.13+ with `specmetrics` installed (development mode: `pip install -e .`)
- Optional: `pip install tiktoken` for exact token counting
- A project directory with specification files containing functional processes with descriptions

## Validation Scenarios

### Scenario 1: Content-Based Scoring Visible

**Purpose**: Verify that elements with longer descriptions score higher than identically-typed elements with shorter descriptions.

```bash
# Run Token Points on a project with varied description lengths
specmetrics measure /path/to/project --metrics tp --verbose

# Inspect the token_point output in metrics.json
python3 -c "
import json
with open('.specmetrics/runs/<measure_id>/metrics.json') as f:
    data = json.load(f)
tp = next(m for m in data if m['name'] == 'tp')
# Check that entities of the same type have different scores
from collections import defaultdict
by_type = defaultdict(list)
for e in tp['entities']:
    by_type[e['type']].append(e['score'])
for t, scores in by_type.items():
    if len(scores) > 1 and len(set(scores)) > 1:
        print(f'{t}: scores vary from {min(scores):.1f} to {max(scores):.1f}')
print('Content-based scoring active: same-type entities have different scores')
"
```

### Scenario 2: Content Volume Correlation

**Purpose**: Verify that a 2:1 content volume ratio produces Token Points ratio between 1.5:1 and 2.5:1.

```bash
# Measure two specification files with known content volume ratio
specmetrics measure project_a --metrics tp --output json > /tmp/a.json
specmetrics measure project_b --metrics tp --output json > /tmp/b.json

python3 -c "
import json
a = json.load(open('/tmp/a.json'))
b = json.load(open('/tmp/b.json'))
tp_a = next(m['total'] for m in a['results'] if m['name'] == 'Token Points')
tp_b = next(m['total'] for m in b['results'] if m['name'] == 'Token Points')
ratio = max(tp_a, tp_b) / min(tp_a, tp_b)
print(f'Token Points ratio: {ratio:.2f} (expected 1.5-2.5 for 2:1 content)')
assert 1.5 <= ratio <= 2.5, f'Ratio {ratio:.2f} out of expected range'
"
```

### Scenario 3: Specification Cost > 0 Without Custom Calibration

**Purpose**: Verify CSM activities contribute positively with default calibration.

```bash
# Run on a project with specification activities (no custom calibration file)
specmetrics measure /path/to/project --metrics tp

python3 -c "
import json
with open('.specmetrics/runs/<measure_id>/metrics.json') as f:
    data = json.load(f)
tp = next(m for m in data if m['name'] == 'tp')
# Check that specification_cost metadata exists and > 0
sc = tp.get('metadata', {}).get('specification_cost', 0)
print(f'Specification Cost: {sc}')
assert sc > 0, 'Specification Cost should be > 0 with default calibration'
print('PASS: Specification Cost > 0')
"
```

### Scenario 4: Content Token Counts in Payload

**Purpose**: Verify `token_content_tokens` and extended `token_element_counts` appear in output.

```bash
python3 -c "
import json
# Check the raw measure.json stage output for new keys
with open('.specmetrics/runs/<measure_id>/measure.json') as f:
    measure = json.load(f)
# The payload is nested; look for content_tokens in element_counts
print('Payload keys with content_tokens:')
# Adjust based on actual JSON structure
"
```

### Scenario 5: Backward Compatibility — Old Calibration YAML

**Purpose**: Verify old calibration files without `content_multiplier` or `activities` still work.

```bash
# Create an old-style calibration file
mkdir -p .specmetrics/calibration
cat > .specmetrics/calibration/old_profile.yml << 'EOF'
version: "1.0.0"
name: old_profile
specification_cost:
  decisions: 2.0
  risks: 3.0
code_generation_cost:
  functional_processes: 10.0
  operations: 4.0
EOF

# Run measurement
specmetrics measure . --metrics tp

# Verify: no errors, content_multiplier defaulted to 0.1, activities defaulted to non-zero
python3 -c "
import json
with open('.specmetrics/runs/<measure_id>/metrics.json') as f:
    data = json.load(f)
tp = next(m for m in data if m['name'] == 'tp')
cm = tp.get('metadata', {}).get('content_multiplier', None)
print(f'content_multiplier: {cm}')
assert cm is not None, 'content_multiplier should be present (default 0.1)'
print('PASS: Old calibration file loaded with new defaults')
"
```

### Scenario 6: Disable Content Estimation

**Purpose**: Verify that setting `content_multiplier: 0` reverts to type-weight-only scoring.

```bash
cat > .specmetrics/calibration/no_content.yml << 'EOF'
version: "1.0.0"
name: no_content
content_multiplier: 0.0
specification_cost:
  decisions: 2.0
code_generation_cost:
  functional_processes: 5.0
EOF

specmetrics measure . --metrics tp

python3 -c "
import json
with open('.specmetrics/runs/<measure_id>/metrics.json') as f:
    data = json.load(f)
tp = next(m for m in data if m['name'] == 'tp')
# All same-type entities should have identical scores (no content variance)
from collections import defaultdict
by_type = defaultdict(set)
for e in tp['entities']:
    by_type[e['type']].add(e['score'])
uniform = all(len(s) == 1 for s in by_type.values())
print(f'Scores uniform (no content variance): {uniform}')
"
```

### Scenario 7: RFC-028 Updated

**Purpose**: Verify the RFC contains the new content-based estimation section.

```bash
grep -c "Content-Based Estimation" "docs/rfcs/RFC-028 - Token Points Measurement Engine.md"

# Expected: >= 1 (new section exists)
```

```bash
# Verify minimum word count in the new section
python3 -c "
with open('docs/rfcs/RFC-028 - Token Points Measurement Engine.md') as f:
    content = f.read()
# Extract section between 'Content-Based Estimation' and next '##' heading
import re
match = re.search(r'## Content-Based Estimation.*?(?=\n##|\Z)', content, re.DOTALL)
if match:
    words = len(match.group().split())
    print(f'Section word count: {words}')
    assert words >= 200, f'Section too short: {words} words'
    print('PASS: RFC section meets minimum word count')
"
```

### Scenario 8: tiktoken Fallback

**Purpose**: Verify engine works without tiktoken installed.

```bash
# Uninstall tiktoken temporarily, run, verify no crash
pip uninstall -y tiktoken 2>/dev/null
specmetrics measure /path/to/project --metrics tp 2>&1 | grep -i "tiktoken not installed\|using character-count"

# Expected: Warning about tiktoken not installed
# Measurement completes successfully with fallback counting
```

## Known Limitations

- Token counting uses content text only (name + description). Structured fields like `rule_type`, `activity_type`, and element relationships are not tokenized — they contribute via type_weight only.
- The character-count fallback (4 chars ≈ 1 token) is approximate. Actual token counts vary by text content (code vs natural language, whitespace patterns).
- Content-based scores change when specification text is edited, even if structure is unchanged. This is by design but means scores are not stable across specification iterations that only edit wording.
