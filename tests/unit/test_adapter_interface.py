from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


from specmetrics.kernel.adapter_interface import Document, DocumentSection


class TestSpecificationAdapterProtocol:
    def test_valid_adapter_passes_isinstance_check(self):
        @runtime_checkable
        class CheckableProtocol(Protocol):
            def scan(self, repository_path: Path) -> list[Document]:
                ...

            def supports(self, path: Path) -> bool:
                ...

        class ValidAdapter:
            def scan(self, repository_path: Path) -> list[Document]:
                return []

            def supports(self, path: Path) -> bool:
                return True

        adapter = ValidAdapter()
        assert isinstance(adapter, CheckableProtocol)

    def test_adapter_missing_scan_fails_protocol_check(self):
        @runtime_checkable
        class CheckableProtocol(Protocol):
            def scan(self, repository_path: Path) -> list[Document]:
                ...

            def supports(self, path: Path) -> bool:
                ...

        class MissingScan:
            def supports(self, path: Path) -> bool:
                return True

        adapter = MissingScan()
        assert not isinstance(adapter, CheckableProtocol)

    def test_adapter_missing_supports_fails_protocol_check(self):
        @runtime_checkable
        class CheckableProtocol(Protocol):
            def scan(self, repository_path: Path) -> list[Document]:
                ...

            def supports(self, path: Path) -> bool:
                ...

        class MissingSupports:
            def scan(self, repository_path: Path) -> list[Document]:
                return []

        adapter = MissingSupports()
        assert not isinstance(adapter, CheckableProtocol)

    def test_mock_adapter_scan_returns_documents(self):
        class MockAdapter:
            def scan(self, repository_path: Path) -> list[Document]:
                return [
                    Document(
                        id="doc-1",
                        path="specs/req.md",
                        document_type="section",
                        content="# Requirement",
                    )
                ]

            def supports(self, path: Path) -> bool:
                return (path / "specs").is_dir()

        adapter = MockAdapter()
        repo_path = Path("/fake/repo")
        docs = adapter.scan(repo_path)
        assert len(docs) == 1
        assert docs[0].id == "doc-1"
        assert docs[0].path == "specs/req.md"
        assert docs[0].document_type == "section"

    def test_mock_adapter_returns_empty_list_for_empty_repository(self):
        class MockAdapter:
            def scan(self, repository_path: Path) -> list[Document]:
                return []

            def supports(self, path: Path) -> bool:
                return True

        adapter = MockAdapter()
        docs = adapter.scan(Path("/empty/repo"))
        assert docs == []


class TestDocumentDataclass:
    def test_document_accepts_valid_field_values(self):
        doc = Document(id="doc-1", path="specs/req.md", document_type="section", content="# Hello")
        assert doc.id == "doc-1"
        assert doc.path == "specs/req.md"
        assert doc.document_type == "section"
        assert doc.content == "# Hello"

    def test_document_preserves_metadata_dict(self):
        meta = {"framework": "openspec", "version": "1.0"}
        doc = Document(
            id="doc-1",
            path="specs/req.md",
            document_type="section",
            content="# Hello",
            metadata=meta,
        )
        assert doc.metadata == meta
        assert doc.metadata["framework"] == "openspec"

    def test_document_section_stores_hierarchy_correctly(self):
        subsection = DocumentSection(id="sub-1", title="Subsection", level=2, content="Sub content")
        section = DocumentSection(
            id="sec-1",
            title="Main Section",
            level=1,
            content="Main content",
            subsections=[subsection],
        )
        assert section.id == "sec-1"
        assert section.level == 1
        assert len(section.subsections) == 1
        assert section.subsections[0].id == "sub-1"
        assert section.subsections[0].level == 2

    def test_document_with_empty_content_is_valid(self):
        doc = Document(id="doc-empty", path="empty.md", document_type="section", content="")
        assert doc.content == ""


class TestMockAdapterScan:
    def test_mock_adapter_scan_returns_documents_with_correct_path_and_type(self):
        class MockAdapter:
            def scan(self, repository_path: Path) -> list[Document]:
                return [
                    Document(id="uc-1", path="specs/use-cases/login.md", document_type="use_case", content="# Login"),
                    Document(id="br-1", path="specs/business-rules/password.md", document_type="business_rule", content="# Password"),
                ]

            def supports(self, path: Path) -> bool:
                return True

        adapter = MockAdapter()
        docs = adapter.scan(Path("/repo"))
        assert len(docs) == 2
        assert docs[0].path == "specs/use-cases/login.md"
        assert docs[0].document_type == "use_case"
        assert docs[1].path == "specs/business-rules/password.md"
        assert docs[1].document_type == "business_rule"
