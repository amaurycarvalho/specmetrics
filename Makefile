VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

.PHONY: venv test build lint

$(VENV):
	python3 -m venv $(VENV)
	$(PIP) install -q --upgrade pip

venv: $(VENV)

test: $(VENV)
	$(PIP) install -q -e .[dev]
	$(PYTHON) -m pytest --tb=short

build: $(VENV)
	$(PIP) install -q build
	$(PYTHON) -m build

lint: $(VENV)
	$(PIP) install -q ruff
	$(VENV)/bin/ruff check .
