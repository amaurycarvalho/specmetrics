# Quickstart: Cognitive Points Improvements

**Feature**: 039-cognitive-points-improvements

## Prerequisites

- Python 3.13+ with `specmetrics` installed (development mode)
- Optional: `pip install tiktoken` for exact token counting
- spec 038 (Token Points) must be implemented first (shared `count_tokens()` dependency)
- A project directory with specification files containing functional processes with descriptions, and BusinessRules with `rule_type` attributes

## Validation Scenarios

### Scenario 1: Content-Based Cognitive Scoring

**Purpose**: Verify elements with longer descriptions score higher than identically-typed elements with shorter descriptions.

```bash
specmetrics measure /path/to/project --metrics cp --verbose

python3 -c "
import json
with open('.specmetrics/runs/<measure_id>/metrics.json') as f:
    data = json.load(f)
cp = next(m for m in data if m['name'] == 'cp')
from collections import defaultdict
by_type = defaultdict(list)
for e in cp['entities']:
    by_type[e['type']].append(e['score'])
varied = {t: (min(s), max(s)) for t, s in by_type.items() if min(s) != max(s)}
print(f'Types with content-based score variance: {list(varied.keys())}')
assert len(varied) > 0, 'No content-based variance detected'
"
```

### Scenario 2: Sub-Type Bloom Classification

**Purpose**: Verify BusinessRules with different `rule_type` values map to different Bloom levels.

```bash
python3 -c "
import json
with open('.specmetrics/runs/<measure_id>/metrics.json') as f:
    data = json.load(f)
cp = next(m for m in data if m['name'] == 'cp')
rules = [e for e in cp['entities'] if e['type'] == 'business_rule']
levels = {(e['metadata'].get('rule_type',''), e['metadata'].get('bloom_level','')) for e in rules}
print(f'BusinessRule (rule_type, bloom_level) pairs: {levels}')
assert len(levels) > 1, 'All BusinessRules mapped to same Bloom level'
"
```

### Scenario 3: Default Bloom Level Changed

**Purpose**: Verify unknown element types default to "understand" (2.0).

```bash
python3 -c "
# Programmatic test: create a BloomClassifier with defaults,
# classify an unknown type, verify level is 'understand'
from specmetrics.plugins.measurement.cognitive_points.bloom_classifier import DefaultBloomClassifier
classifier = DefaultBloomClassifier()
level = classifier.classify('unknown_element_type')
assert level == 'understand', f'Expected understand, got {level}'
print(f'PASS: unknown type defaults to {level}')
"
```

### Scenario 4: Content Disabled with multiplier=0

**Purpose**: Verify setting `content_multiplier: 0` reverts to pure Bloom taxonomy scoring.

```bash
mkdir -p .specmetrics/calibration
cat > .specmetrics/calibration/cp_no_content.yml << 'EOF'
version: "1.0"
name: no_content_cognitive
content_multiplier: 0.0
EOF

specmetrics measure /path/to/project --metrics cp

python3 -c "
import json
with open('.specmetrics/runs/<measure_id>/metrics.json') as f:
    data = json.load(f)
cp = next(m for m in data if m['name'] == 'cp')
from collections import defaultdict
by_type = defaultdict(set)
for e in cp['entities']:
    by_type[e['type']].add(e['score'])
uniform = all(len(s) == 1 for s in by_type.values())
print(f'All same-type scores uniform (content disabled): {uniform}')
"
```

### Scenario 5: Content Token Counts in Payload

**Purpose**: Verify `cognitive_content_tokens` and `cognitive_content_multiplier` appear in output.

```bash
python3 -c "
import json
with open('.specmetrics/runs/<measure_id>/metrics.json') as f:
    data = json.load(f)
cp = next(m for m in data if m['name'] == 'cp')
cm = cp.get('metadata', {}).get('content_multiplier', None)
ct = cp.get('metadata', {}).get('content_tokens', None)
print(f'content_multiplier: {cm}')
print(f'total content tokens: {ct}')
assert cm is not None, 'Missing content_multiplier in metadata'
"
```

### Scenario 6: Cross-Framework Comparability

**Purpose**: Verify SpecKit and OpenSpec specs with similar content produce similar scores.

```bash
# Run on two specs from different frameworks with similar content
specmetrics measure spec_kit_project --metrics cp --output json > /tmp/speckit.json
specmetrics measure open_spec_project --metrics cp --output json > /tmp/openspec.json

python3 -c "
import json
a = json.load(open('/tmp/speckit.json'))
b = json.load(open('/tmp/openspec.json'))
# Compare raw scores
# (Acceptance: within 15% if content volumes are similar)
"
```

### Scenario 7: RFC-029 Updated

```bash
grep -c "Content-Based Estimation" "docs/rfcs/RFC-029 - Cognitive Points Measurement Engine.md"
# Expected: >= 1

python3 -c "
with open('docs/rfcs/RFC-029 - Cognitive Points Measurement Engine.md') as f:
    content = f.read()
import re
match = re.search(r'## Content-Based Estimation.*?(?=\n##|\Z)', content, re.DOTALL)
if match:
    words = len(match.group().split())
    print(f'Section word count: {words}')
    assert words >= 200, f'Too short: {words} words'
    print('PASS')
"
```

### Scenario 8: Backward Compatibility

**Purpose**: Old calibration YAML without `content_multiplier` still works.

```bash
cat > .specmetrics/calibration/old_cp.yml << 'EOF'
version: "1.0"
name: old_cognitive
bloom_levels:
  remember: 1.0
  understand: 2.0
  apply: 3.0
  analyze: 4.0
  evaluate: 5.0
  create: 8.0
EOF

specmetrics measure /path/to/project --metrics cp
# Expected: No errors. content_multiplier defaults to 0.1.
# Bloom mappings use defaults with sub-types.
```

## Known Limitations

- Sub-type classification depends on `rule_type` and `operation_type` metadata being present on CSM/CFM elements. If extraction doesn't populate these attributes, the base type mapping is used.
- Content token counting is identical between Token Points and Cognitive Points — only the Bloom weight differs.
- The Fibonacci normalizer ceiling (100) still exists; very large specifications may hit it. Raw score is always available.
- Element name truncation at 80 characters (current behavior) should be removed or increased.
