from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field, SecretStr

from .sources import SourceLevel


class PipelineSettings(BaseModel):
    stage_timeout: int = Field(60, ge=1, le=3600, description="Seconds per pipeline stage")
    fail_fast: bool = Field(True, description="Stop on first stage failure")


class LoggingSettings(BaseModel):
    level: str = Field("info", description="Log level: debug, info, warning, error")
    format: str = Field("console", description="Log format: console, json")


class SecuritySettings(BaseModel):
    api_key: SecretStr | None = Field(None, description="API key for external services", json_schema_extra={"sensitive": True})
    tls_ca_cert_path: str | None = Field(None, description="Path to CA certificate bundle")


class RunArtifactsSettings(BaseModel):
    max_entities_per_stage: int = Field(5000, ge=1, description="Max entities per stage JSON artifact before truncation")


class CoreConfig(BaseModel):
    pipeline: PipelineSettings = Field(default_factory=PipelineSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    run_artifacts: RunArtifactsSettings = Field(default_factory=RunArtifactsSettings)


@runtime_checkable
class ConfigProvider(Protocol):
    def get(self, key: str, default: Any = ...) -> Any: ...
    def get_model(self, model_type: type) -> Any: ...
    @property
    def dump(self) -> ConfigurationDump: ...
    @property
    def warnings(self) -> list[ConfigWarning]: ...


@dataclass
class SourceProvenance:
    key: str
    source: str
    level: SourceLevel
    is_default: bool = False


@dataclass
class ConfigWarning:
    message: str
    key: str | None = None
    source: str | None = None


@dataclass
class DumpEntry:
    key: str
    value: Any
    source: str
    level: str
    is_default: bool = False
    is_sensitive: bool = False


@dataclass
class ConfigurationDump:
    entries: list[DumpEntry] = field(default_factory=list)
    warnings: list[ConfigWarning] = field(default_factory=list)
    sources_loaded: list[str] = field(default_factory=list)


@dataclass
class ResolvedConfiguration:
    values: CoreConfig
    provenance: dict[str, SourceProvenance] = field(default_factory=dict)
    warnings: list[ConfigWarning] = field(default_factory=list)
    schema: type[CoreConfig] = CoreConfig
