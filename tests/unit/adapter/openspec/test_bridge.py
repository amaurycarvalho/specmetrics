from __future__ import annotations

from specmetrics.kernel.events import EventType
from specmetrics.kernel.plugin_metadata import PluginType
from specmetrics.plugins.adapter.openspec.bridge import (
    CanonicalModelBuiltHandler,
    DocumentsValidatedHandler,
    create_canonical_model_built_metadata,
    create_documents_validated_metadata,
)


class TestDocumentsValidatedHandlerIdentity:
    """Kills survivors in ``DocumentsValidatedHandler.__init__`` (mutmut_1..7)."""

    def test_init_identity_attributes(self) -> None:
        handler = DocumentsValidatedHandler()
        assert handler.handled_event_type == EventType.DOCUMENTS_VALIDATED
        assert handler.handler_id == "documents_validated_bridge"
        assert handler.stage_name == "documents_validated"

    def test_handle_marks_documents_validated(self) -> None:
        from specmetrics.kernel.pipeline_context import PipelineContext

        context = PipelineContext(adapter_result={"documents": [1, 2, 3]})
        handler = DocumentsValidatedHandler()
        updated = handler.handle(
            type(
                "Event",
                (),
                {
                    "context": context,
                    "event_type": EventType.DOCUMENTS_VALIDATED,
                },
            )()
        )
        assert updated.adapter_result["validated"] is True
        assert updated.adapter_result["document_count"] == 3


class TestCanonicalModelBuiltHandlerIdentity:
    """Kills survivors in ``CanonicalModelBuiltHandler.__init__`` (mutmut_1..7)."""

    def test_init_identity_attributes(self) -> None:
        handler = CanonicalModelBuiltHandler()
        assert handler.handled_event_type == EventType.CANONICAL_MODEL_BUILT
        assert handler.handler_id == "canonical_model_built_bridge"
        assert handler.stage_name == "canonical_model_built"

    def test_handle_returns_context_unchanged(self) -> None:
        from specmetrics.kernel.pipeline_context import PipelineContext

        context = PipelineContext()
        handler = CanonicalModelBuiltHandler()
        updated = handler.handle(
            type(
                "Event",
                (),
                {
                    "context": context,
                    "event_type": EventType.CANONICAL_MODEL_BUILT,
                },
            )()
        )
        assert updated is context


class TestCreateDocumentsValidatedMetadata:
    """Kills survivors in ``create_documents_validated_metadata``."""

    def test_full_metadata(self) -> None:
        meta = create_documents_validated_metadata()
        assert meta.id == "documents_validated_bridge"
        assert meta.api_version == "0.1.0"
        assert meta.plugin_type == PluginType.ADAPTER
        assert meta.handled_event_types == (EventType.DOCUMENTS_VALIDATED,)
        assert isinstance(meta.handler_factory(), DocumentsValidatedHandler)
        assert meta.name == "Documents Validated Bridge"
        assert meta.description == "Acknowledges and logs document validation results"
        assert meta.version == "0.1.0"


class TestCreateCanonicalModelBuiltMetadata:
    """Kills survivors in ``create_canonical_model_built_metadata``."""

    def test_full_metadata(self) -> None:
        meta = create_canonical_model_built_metadata()
        assert meta.id == "canonical_model_built_bridge"
        assert meta.api_version == "0.1.0"
        assert meta.plugin_type == PluginType.ADAPTER
        assert meta.handled_event_types == (EventType.CANONICAL_MODEL_BUILT,)
        assert isinstance(meta.handler_factory(), CanonicalModelBuiltHandler)
        assert meta.name == "Canonical Model Built Bridge"
        assert meta.description == (
            "Acknowledges canonical model built event and logs results"
        )
        assert meta.version == "0.1.0"
