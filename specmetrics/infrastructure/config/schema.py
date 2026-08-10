"""Schemas and protocols for configuration management."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, Self, runtime_checkable

from pydantic import BaseModel, Field, SecretStr

from .sources import SourceLevel


class PipelineSettings(BaseModel):
    """Runtime settings for the pipeline."""

    stage_timeout: int = Field(
        60, ge=1, le=3600, description="Seconds per pipeline stage"
    )
    fail_fast: bool = Field(True, description="Stop on first stage failure")


class LoggingSettings(BaseModel):
    """Logging configuration for the application."""

    level: str = Field("info", description="Log level: debug, info, warning, error")
    format: str = Field("console", description="Log format: console, json")


class SecuritySettings(BaseModel):
    """Security-related configuration values."""

    api_key: SecretStr | None = Field(
        None,
        description="API key for external services",
        json_schema_extra={"sensitive": True},
    )
    tls_ca_cert_path: str | None = Field(
        None, description="Path to CA certificate bundle"
    )


class RunArtifactsSettings(BaseModel):
    """Settings controlling persisted run artifacts."""

    max_entities_per_stage: int = Field(
        5000, ge=1, description="Max entities per stage JSON artifact before truncation"
    )


class CoreConfig(BaseModel):
    """Top-level validated configuration model."""

    pipeline: PipelineSettings = Field(default_factory=PipelineSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    run_artifacts: RunArtifactsSettings = Field(default_factory=RunArtifactsSettings)


@runtime_checkable
class ConfigProvider(Protocol):
    """Protocol for objects that expose resolved configuration values."""

    def get(self: Self, key: str, default: object = ...) -> object:
        """Return the value for a dotted key, or ``default`` when missing."""
        ...

    def get_model(self: Self, model_type: type) -> object:
        """Return the resolved configuration as the given model type."""
        ...

    @property
    def dump(self: Self) -> ConfigurationDump:
        """Return an introspectable dump of the configuration."""
        ...

    @property
    def warnings(self: Self) -> list[ConfigWarning]:
        """Return loading and validation warnings."""
        ...


@dataclass
class SourceProvenance:
    """Provenance of a single resolved configuration key."""

    key: str
    source: str
    level: SourceLevel
    is_default: bool = False


@dataclass
class ConfigWarning:
    """A non-fatal warning produced while loading or validating configuration."""

    message: str
    key: str | None = None
    source: str | None = None


@dataclass
class DumpEntry:
    """A single flattened configuration entry in a dump."""

    key: str
    value: Any
    source: str
    level: str
    is_default: bool = False
    is_sensitive: bool = False


@dataclass
class ConfigurationDump:
    """Full dump of the resolved configuration."""

    entries: list[DumpEntry] = field(default_factory=list)
    warnings: list[ConfigWarning] = field(default_factory=list)
    sources_loaded: list[str] = field(default_factory=list)


@dataclass
class ResolvedConfiguration:
    """Resolved configuration values with provenance and warnings."""

    values: CoreConfig
    provenance: dict[str, SourceProvenance] = field(default_factory=dict)
    warnings: list[ConfigWarning] = field(default_factory=list)
    schema: type[CoreConfig] = CoreConfig
