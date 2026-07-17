VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

.PHONY: venv install test build lint

$(VENV):
	python3 -m venv $(VENV)
	$(PIP) install -q --upgrade pip

venv: $(VENV)

install: $(VENV)
	$(PIP) install -e .

test: $(VENV)
	$(PIP) install -q -e .[dev]
	$(PYTHON) -m pytest --tb=short

build: $(VENV)
	$(PIP) install -q build
	$(PYTHON) -m build

lint: $(VENV)
	$(PIP) install -q ruff
	$(VENV)/bin/ruff check .
