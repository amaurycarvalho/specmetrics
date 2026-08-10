"""Kernel package: evidence graph, canonical model builders, and the pipeline engine."""

from .adapter_interface import Document, DocumentSection, SpecificationAdapter
from .adapter_registry import AdapterRegistry
from .cfm.builder import CfmBuilderStage, build
from .cfm.classifier import classify_node, strip_framework_labels
from .cfm.metadata import BuildMetadata, ClassificationConflict
from .cfm.model import (
    Actor,
    ActorType,
    BusinessRule,
    CanonicalFunctionalModel,
    DataGroup,
    DataType,
    EvidenceRef,
    FunctionalProcess,
    Operation,
    Relationship,
    RelationshipType,
    RuleType,
    UnclassifiedElement,
)
from .deterministic_engine import DeterministicSemanticEngine
from .diagnostics import (
    Diagnostics,
    StageStatus,
    StageTiming,
)
from .diagnostics import (
    StageError as StageErrorRecord,
)
from .engine_patterns import PatternLibrary
from .engine_rule import ExtractionRule, RulePackLoader
from .engine_visitors import (
    CodeBlockVisitor,
    EmphasisVisitor,
    ExtractionState,
    HeadingVisitor,
    LinkVisitor,
    ListVisitor,
    Observation,
    ParagraphVisitor,
    QuoteVisitor,
    TableVisitor,
)
from .events import EventType, PipelineEvent
from .evidence_graph import (
    EdgeAlreadyExistsError,
    EvidenceGraph,
    EvidenceGraphError,
    GraphBackend,
    GraphEdge,
    GraphMetadata,
    GraphNode,
    InvalidGraphDataError,
    NodeAlreadyExistsError,
    NodeNotFoundError,
    SelfLoopError,
    fingerprint_node,
)
from .evidence_graph_stage import EvidenceGraphStage, NetworkXBackend
from .exceptions import HandlerNotFoundError, PipelineError, PluginError, StageError
from .extraction_provider import (
    EvidenceReference,
    ExtractedElement,
    ExtractionProvider,
    ExtractionResult,
    ProcessingStats,
)
from .extraction_registry import ProviderRouter
from .extraction_stage import ExtractionStage
from .graph_persistence import GraphStore
from .graph_query_engine import GraphQueryEngine
from .handler_registry import EventHandler, HandlerRegistry
from .pipeline_context import PipelineContext
from .pipeline_engine import PipelineEngine
from .plugin_discovery import PluginDiscovery, load_plugins
from .plugin_metadata import PluginMetadata, PluginStatus, PluginType
from .plugin_registry import PluginDescriptor, PluginRegistry
from .plugin_validation import PluginValidator, ValidationResult
from .semantic_extraction_engine import (
    SemanticEngineFactory,
    SemanticExtractionEngine,
)

__all__ = [
    "Actor",
    "ActorType",
    "AdapterRegistry",
    "BuildMetadata",
    "BusinessRule",
    "CanonicalFunctionalModel",
    "CfmBuilderStage",
    "ClassificationConflict",
    "CodeBlockVisitor",
    "DataGroup",
    "DataType",
    "DeterministicSemanticEngine",
    "Diagnostics",
    "Document",
    "DocumentSection",
    "EdgeAlreadyExistsError",
    "EmphasisVisitor",
    "EventHandler",
    "EventType",
    "EvidenceGraph",
    "EvidenceGraphError",
    "EvidenceGraphStage",
    "EvidenceRef",
    "EvidenceReference",
    "ExtractedElement",
    "ExtractionError",
    "ExtractionProvider",
    "ExtractionResult",
    "ExtractionRule",
    "ExtractionStage",
    "ExtractionState",
    "FunctionalProcess",
    "GraphBackend",
    "GraphEdge",
    "GraphMetadata",
    "GraphNode",
    "GraphQueryEngine",
    "GraphStore",
    "HandlerNotFoundError",
    "HandlerRegistry",
    "HeadingVisitor",
    "InvalidGraphDataError",
    "LinkVisitor",
    "ListVisitor",
    "LiteLLMSemanticEngine",
    "NetworkXBackend",
    "NodeAlreadyExistsError",
    "NodeNotFoundError",
    "Observation",
    "Operation",
    "ParagraphVisitor",
    "PatternLibrary",
    "PipelineContext",
    "PipelineEngine",
    "PipelineError",
    "PipelineEvent",
    "PluginDescriptor",
    "PluginDiscovery",
    "PluginError",
    "PluginMetadata",
    "PluginRegistry",
    "PluginStatus",
    "PluginType",
    "PluginValidator",
    "ProcessingStats",
    "ProviderRouter",
    "QuoteVisitor",
    "Relationship",
    "RelationshipType",
    "RulePackLoader",
    "RuleType",
    "SelfLoopError",
    "SemanticEngineFactory",
    "SemanticExtractionEngine",
    "SpecificationAdapter",
    "StageError",
    "StageErrorRecord",
    "StageStatus",
    "StageTiming",
    "TableVisitor",
    "UnclassifiedElement",
    "ValidationResult",
    "build",
    "classify_node",
    "fingerprint_node",
    "load_plugins",
    "strip_framework_labels",
]

_LAZY_LITELLM_NAMES = frozenset({"ExtractionError", "LiteLLMSemanticEngine"})


def __getattr__(name: str) -> object:
    """Resolve the LiteLLM engine symbols lazily.

    Importing ``litellm_engine`` eagerly pulls in litellm (an expensive import),
    so those names are resolved only when actually accessed.
    """
    if name in _LAZY_LITELLM_NAMES:
        from . import litellm_engine

        return getattr(litellm_engine, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
