VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

.PHONY: venv test build lint

$(VENV):
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

venv: $(VENV)

test: $(VENV)
	$(PIP) install -e .[dev]
	$(PYTHON) -m pytest --tb=short

build: $(VENV)
	$(PIP) install build
	$(PYTHON) -m build

lint: $(VENV)
	$(PIP) install ruff
	$(VENV)/bin/ruff check .
