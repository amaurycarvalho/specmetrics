VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
FLAKE8 = $(VENV)/bin/flake8

.PHONY: venv install test build lint install-quality-tools quality-gate complexity duplication mutation-run mutation-check mutation-results mutation-stats security security-all security-changed

$(VENV):
	python3 -m venv $(VENV)
	$(PIP) install -q --upgrade pip

venv: $(VENV)

install: $(VENV)
	$(PIP) install -e .

build: $(VENV)
	$(PIP) install -q build
	$(PYTHON) -m build

test: $(VENV)
	$(PIP) install -q -e .[dev]
	$(PYTHON) -m pytest --tb=short --cov=. --cov-report=xml:coverage.xml --cov-report=term-missing --cov-fail-under=85

lint: $(VENV)
	$(PIP) install -q -U .[dev]
	$(VENV)/bin/ruff check specmetrics/
	$(FLAKE8) --max-complexity=10 --select=B,A,D --extend-exclude=specmetrics/tests ./specmetrics/

install-quality-tools: $(VENV)
	$(PIP) install -q -U .[quality]
	npm install -g jscpd@4.0.1
	mkdir -p mutants/

quality-gate: $(VENV)
	$(MAKE) install-quality-tools
	$(MAKE) lint
	$(MAKE) complexity
	$(MAKE) duplication
	$(MAKE) test
	$(MAKE) mutation-check
	$(MAKE) security

complexity: $(VENV)
	@echo "Checking complexity metrics..."
	@$(VENV)/bin/radon cc -a -nb -i "tests,build,dist,ccache,mutants,.venv" -s specmetrics/
	@$(PYTHON) scripts/complexity_metrics.py || exit 1
	@$(VENV)/bin/xenon --max-absolute=B --max-modules=B --max-average=B --ignore "tests,build,dist,ccache,mutants,.venv" specmetrics/ || exit 1
	@$(VENV)/bin/lizard --CCN 10 --length 80 --warnings_only -x "./tests/*" -x "./build/*" -x "./dist/*" -x "./ccache/*" -x "./mutants/*" -x "./.venv/*" -x "./.opencode/*" -x "./specmetrics/tests/*" specmetrics/ || true

duplication: $(VENV)
	@echo "Checking code duplication..."
	@if jscpd --pattern "**/*.py" --threshold 10 --format python --ignore "**/tests/**" --ignore "**/.venv/**" --ignore "**/build/**" --ignore "**/dist/**" --ignore "**/__pycache__/**" --ignore "**/mutants/**" --ignore "**/.opencode/**" specmetrics scripts --silent >/dev/null 2>&1; then \
		jscpd --pattern "**/*.py" --threshold 7 --format python --ignore "**/tests/**" --ignore "**/.venv/**" --ignore "**/build/**" --ignore "**/dist/**" --ignore "**/__pycache__/**" --ignore "**/mutants/**" --ignore "**/.opencode/**" specmetrics scripts --silent >/dev/null 2>&1 && \
		(echo "Duplication OK (<= 7%)") || \
		(echo "WARNING: duplication between 7% and 10%"); \
	else \
		echo "BLOCKING: duplication > 10%"; exit 1; \
	fi

mutation-run: $(VENV)
	@echo "Running mutation tests..."
	@$(VENV)/bin/mutmut run
	@$(MAKE) mutation-stats

mutation-stats: $(VENV)
	@echo "Exporting mutation stats..."
	@$(VENV)/bin/mutmut export-cicd-stats
	@$(PYTHON) scripts/check-mutation-score.py || exit 0

mutation-results: $(VENV)
	@echo "Generating mutation tests results..."
	@echo "--------------Mutation tests results--------------" > mutants/mutmut-cicd-results.log
	@$(PYTHON) scripts/check-mutation-score.py >> mutants/mutmut-cicd-results.log || exit 0
	@echo "--------------Mutation tests logs-----------------" >> mutants/mutmut-cicd-results.log
	@$(VENV)/bin/mutmut results | grep "survived" | cut -d':' -f1 | while read -r mutant; do \
		.venv/bin/mutmut show "$$mutant" >> mutants/mutmut-cicd-results.log; \
	done || exit 0
	@echo "Mutation tests results saved to mutants/mutmut-cicd-results.log"
	@echo "Lines count: $$(wc -l < mutants/mutmut-cicd-results.log)"
	@echo "\n============ SUMMARY ============="
	@echo "\n--- START (first 9 lines) ---"
	@head -n 9 mutants/mutmut-cicd-results.log
	@echo "\n--- END (last 10 lines) ---"
	@tail -n 10 mutants/mutmut-cicd-results.log
	@echo "===================================="

mutation-check:
	@echo "Checking mutation tests..."
	@$(PYTHON) scripts/check-mutation-score.py

security: security-all

security-changed: $(VENV)
	@echo "Running security checks on changed files..."
	@$(VENV)/bin/semgrep ci --oss-only --quiet --config auto --include "specmetrics/" || exit 1

security-all: $(VENV)
	@echo "Running security checks..."
	@$(VENV)/bin/semgrep scan --oss-only --quiet --config auto --severity ERROR --error specmetrics/ || exit 1
	@echo "Medium-severity findings (non-blocking):"
	@$(VENV)/bin/semgrep scan --oss-only --quiet --config auto --severity WARNING --json specmetrics/ 2>/dev/null | $(PYTHON) -c "import json,sys; d=json.load(sys.stdin); n=len(d.get('results',[])); print(f'  {n} medium finding(s)')" || true