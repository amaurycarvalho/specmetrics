# SpecMetrics

A Functional Measurement Engine for Spec Driven Development (SDD)

[![Spec-Driven Development](https://img.shields.io/badge/SDD-SpecKit-yellow)](.specify/memory/constitution.md)

---

## Vision

**SpecMetrics** is an Open Source **Functional Measurement Engine** for **Specification Driven Development (SDD)**.

Its purpose is to transform software specifications into structured, traceable and measurable engineering assets, enabling deterministic functional measurement directly from specification artifacts instead of source code or manually interpreted requirements.

SpecMetrics leverages Large Language Models to semantically understand specifications produced by frameworks such as OpenSpec and SpecKit, extracting evidence-based functional knowledge that is normalized into a canonical internal representation. This representation is then consumed by deterministic measurement engines capable of applying different functional sizing methodologies while preserving traceability and explainability.

Beyond functional measurement, SpecMetrics provides a foundation for engineering observability by exposing structured functional information that can be consumed by dashboards, DevOps platforms, software quality tools and AI-assisted development workflows through an extensible plugin ecosystem.

## How it Works

### Input Specs

- [OpenSpec](https://github.com/Fission-AI/openspec);
- [SpecKit](https://github.com/github/spec-kit).

### Evaluate Metrics

- [Function Point Analysis (IFPUG/FPA)](https://ifpug.org/ifpug-standards/fpa);
- [Simplified Function Point (IFPUG/SFP)](https://ifpug.org/ifpug-standards/sfp);
- [Software Non-Functional Assessment Process (IFPUG/SNAP)](https://ifpug.org/ifpug-standards/snap).

> **Note:** The current implementations of **FPA**, **SFP**, and **SNAP** are **draft prototypes** intended solely for demonstration and validation purposes. They provide a highly simplified approximation of their respective measurement methodologies and **do not constitute complete or standards-compliant implementations**. Full conformance with the official specifications requires additional counting rules, validation logic, and methodological details beyond the scope of these prototype implementations.

### Output Formats

- JSON
- CSV
- XML
- Markdown

---

## 🧑‍💻 For Users

### How to Install

Download the wheel from [Releases](https://github.com/amaurycarvalho/specmetrics/releases).

After, use the command below to install it.

```bash
uv tool install specmetrics-<version>-py3-none-any.whl
```

or

```bash
pipx install --force specmetrics-<version>-py3-none-any.whl
```

### How to Use

```bash
specmetrics --help
specmetrics measure --help
specmetrics plugins --help
specmetrics plugins list --help
```

---

## 👨‍🔧 For Developers

### How to Get the Source Code

```bash
git clone https://github.com/amaurycarvalho/specmetrics.git
```

### How to Build

```bash
make build
```

#### Linting and Unit Testing

```bash
make lint test
```

### How to Test (e2e)

```bash
.venv/bin/specmetrics --help
```

---

### Know More

You can find more information [here](docs/PRD.md) and [here](docs/system%20designs/Foundation.md).

All specs can be found [here](specs/).
