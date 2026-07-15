# Exporter Plugin Interface Contract

**Phase 1 output for `/speckit.plan` command**

---

## Purpose

Defines the contract that custom export format plugins must implement to integrate
with the SpecMetrics export layer.

---

## Plugin Discovery

Exporters are discovered via Python entry points under the `specmetrics.exporters`
group, matching the existing plugin registry pattern.

```python
# pyproject.toml (example for a custom TOML exporter)
[project.entry-points."specmetrics.exporters"]
toml = "myplugin.toml_exporter:TomlExporter"
```

---

## Interface: `ExporterPlugin`

### Methods

#### `format_id() -> str`

Returns the unique identifier for this format (e.g., `"json"`, `"csv"`).
Must match the entry point name and be lowercase alphanumeric with hyphens.

#### `file_extension() -> str`

Returns the default file extension including leading dot (e.g., `".json"`, `".csv"`).

#### `content_type() -> str`

Returns the MIME content type (e.g., `"application/json"`, `"text/csv"`).

#### `export(measurements: list[Measurement], evidence_refs: list[EvidenceRef], metadata: ExportMetadata, output: IO) -> None`

Serializes the provided measurements and writes to the output stream.

| Parameter | Type | Description |
|-----------|------|-------------|
| `measurements` | `list[Measurement]` | Canonical measurement records from CFM |
| `evidence_refs` | `list[EvidenceRef]` | Traceability evidence references |
| `metadata` | `ExportMetadata` | Run metadata (version, run ID, timestamp) |
| `output` | `IO` | Writable byte stream (file or stdout) |

**Behavior requirements**:
- Must produce valid output for list of any length (including empty).
- Must include all evidence references for traceability (FR-002).
- Must include export metadata (FR-010).
- Must raise `ExportError` (or subclass) for unrecoverable failures.
- Should not catch and suppress errors that indicate programming bugs.
- Must not modify the input `measurements` or `evidence_refs` lists.

**Error handling**:
- `ExportError`: Base exception for export failures. Message is surfaced to the user.
- Plugin must not write partial output before raising `ExportError`.
- Plugin must close/release any resources it acquired on error.

---

## Configuration Schema

Each exporter plugin may define configuration options via a Pydantic model:

```python
class ExporterConfig(BaseModel):
    """Base config — override in subclasses for plugin-specific options."""
    indent: int = 2
    encoding: str = "utf-8"
```

Plugins expose their config schema via a class method:

```python
@classmethod
def config_schema(cls) -> type[BaseModel]:
    return ExporterConfig
```

---

## Registration Flow

1. Plugin registry scans `specmetrics.exporters` entry points.
2. Each entry point is instantiated and validated against the `ExporterPlugin` interface.
3. Format ID uniqueness is verified across all registered exporters.
4. A `FormatRegistration` record is created and made available for CLI/MCP selection.

---

## Built-in Implementations

| Format | Plugin ID | Entry Point |
|--------|-----------|-------------|
| JSON | `json` | `specmetrics.plugins.exporter.json_exporter:JsonExporter` |
| CSV | `csv` | `specmetrics.plugins.exporter.csv_exporter:CsvExporter` |
| XML | `xml` | `specmetrics.plugins.exporter.xml_exporter:XmlExporter` |
