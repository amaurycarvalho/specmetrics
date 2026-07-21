from __future__ import annotations

from pathlib import Path

from specmetrics.kernel.adapter_interface import (
    Document,
    DocumentSection,
    SpecificationAdapter,
    discover_documents,
    infer_document_type,
    read_document_safe,
)


class _ValidMockAdapter:
    @property
    def supported_document_types(self) -> list[str]:
        return ["use_case", "business_rule"]

    def scan(self, repository_path: Path) -> list[Document]:
        return [
            Document(
                id="doc-1",
                path="specs/uc-01.md",
                document_type="use_case",
                content="# Use Case 1",
            )
        ]

    def supports(self, path: Path) -> bool:
        return (path / "specs").is_dir()


class _NoScanAdapter:
    @property
    def supported_document_types(self) -> list[str]:
        return []

    def supports(self, path: Path) -> bool:
        return True


class _NoSupportsAdapter:
    @property
    def supported_document_types(self) -> list[str]:
        return []

    def scan(self, repository_path: Path) -> list[Document]:
        return []


class TestProtocolCompliance:
    def test_valid_adapter_passes_isinstance_check(self) -> None:
        adapter = _ValidMockAdapter()
        assert isinstance(adapter, SpecificationAdapter)

    def test_adapter_missing_scan_fails_isinstance_check(self) -> None:
        adapter = _NoScanAdapter()
        assert not isinstance(adapter, SpecificationAdapter)

    def test_adapter_missing_supports_fails_isinstance_check(self) -> None:
        adapter = _NoSupportsAdapter()
        assert not isinstance(adapter, SpecificationAdapter)

    def test_adapter_missing_supported_document_types_fails_isinstance_check(
        self,
    ) -> None:
        class _NoDocTypes:
            def scan(self, repository_path: Path) -> list[Document]:
                return []

            def supports(self, path: Path) -> bool:
                return True

        assert not isinstance(_NoDocTypes(), SpecificationAdapter)

    def test_protocol_is_not_instantiable_directly(self) -> None:
        with_missing = {k for k in ("scan", "supports", "supported_document_types")}
        protocol_members = {
            name for name in dir(SpecificationAdapter) if not name.startswith("_")
        }
        assert protocol_members.issuperset(with_missing)


class TestDocument:
    def test_valid_document(self) -> None:
        doc = Document(
            id="uc-01",
            path="specs/uc-01.md",
            document_type="use_case",
            content="# Use Case 1\nSome description",
        )
        assert doc.id == "uc-01"
        assert doc.path == "specs/uc-01.md"
        assert doc.document_type == "use_case"
        assert doc.content == "# Use Case 1\nSome description"
        assert doc.metadata is None
        assert doc.sections is None

    def test_document_preserves_metadata(self) -> None:
        metadata = {"framework": "openspec", "version": "1.0", "author": "dev"}
        doc = Document(
            id="br-001",
            path="rules/br-001.md",
            document_type="business_rule",
            content="Rule content",
            metadata=metadata,
        )
        assert doc.metadata == metadata
        assert doc.metadata["framework"] == "openspec"

    def test_document_with_empty_content_is_valid(self) -> None:
        doc = Document(
            id="empty-doc",
            path="empty.md",
            document_type="section",
            content="",
        )
        assert doc.content == ""

    def test_document_is_frozen(self) -> None:
        doc = Document(
            id="frozen-test",
            path="test.md",
            document_type="unknown",
            content="content",
        )
        import dataclasses

        assert dataclasses.fields(doc)
        assert dataclasses.is_dataclass(doc)


class TestDocumentSection:
    def test_section_with_fields(self) -> None:
        section = DocumentSection(
            id="sec-1",
            title="Introduction",
            level=1,
            content="Intro content",
        )
        assert section.id == "sec-1"
        assert section.title == "Introduction"
        assert section.level == 1
        assert section.content == "Intro content"
        assert section.subsections is None

    def test_section_stores_hierarchy_correctly(self) -> None:
        subsection = DocumentSection(
            id="sec-1-1",
            title="Background",
            level=2,
            content="Background content",
        )
        parent = DocumentSection(
            id="sec-1",
            title="Introduction",
            level=1,
            content="Intro content",
            subsections=[subsection],
        )
        assert parent.subsections is not None
        assert len(parent.subsections) == 1
        assert parent.subsections[0].id == "sec-1-1"
        assert parent.subsections[0].level == 2

    def test_nested_subsections(self) -> None:
        leaf = DocumentSection(
            id="sec-1-1-1", title="Detail", level=3, content="Detail content"
        )
        child = DocumentSection(
            id="sec-1-1",
            title="Subsection",
            level=2,
            content="Sub content",
            subsections=[leaf],
        )
        root = DocumentSection(
            id="sec-1",
            title="Root",
            level=1,
            content="Root content",
            subsections=[child],
        )
        assert root.subsections[0].subsections[0].id == "sec-1-1-1"
        assert root.subsections[0].subsections[0].level == 3


class TestDiscoverDocuments:
    def test_returns_matching_files(self, tmp_path: Path) -> None:
        (tmp_path / "specs").mkdir()
        (tmp_path / "specs" / "uc-01.md").write_text("hello")
        (tmp_path / "specs" / "br-01.md").write_text("world")
        (tmp_path / "readme.txt").write_text("ignore me")
        result = discover_documents(tmp_path, patterns=("*.md",))
        paths = {str(p.relative_to(tmp_path)) for p in result}
        assert "specs/uc-01.md" in paths
        assert "specs/br-01.md" in paths
        assert "readme.txt" not in paths

    def test_empty_directory_returns_empty_list(self, tmp_path: Path) -> None:
        result = discover_documents(tmp_path)
        assert result == []

    def test_nested_subdirectories_are_included(self, tmp_path: Path) -> None:
        (tmp_path / "a" / "b" / "c").mkdir(parents=True)
        (tmp_path / "a" / "b" / "c" / "doc.md").write_text("nested")
        (tmp_path / "a" / "doc.md").write_text("shallow")
        result = discover_documents(tmp_path, patterns=("*.md",))
        paths = {str(p.relative_to(tmp_path)) for p in result}
        assert "a/doc.md" in paths
        assert "a/b/c/doc.md" in paths

    def test_multiple_patterns(self, tmp_path: Path) -> None:
        (tmp_path / "a.md").write_text("md")
        (tmp_path / "b.yml").write_text("yml")
        (tmp_path / "c.yaml").write_text("yaml")
        (tmp_path / "d.txt").write_text("txt")
        result = discover_documents(tmp_path, patterns=("*.md", "*.yml", "*.yaml"))
        paths = {str(p.relative_to(tmp_path)) for p in result}
        assert "a.md" in paths
        assert "b.yml" in paths
        assert "c.yaml" in paths
        assert "d.txt" not in paths


class TestReadDocumentSafe:
    def test_reads_text_file(self, tmp_path: Path) -> None:
        p = tmp_path / "hello.md"
        p.write_text("Hello, world!", encoding="utf-8")
        assert read_document_safe(p) == "Hello, world!"

    def test_returns_none_for_missing_file(self) -> None:
        assert read_document_safe(Path("/nonexistent/file.md")) is None

    def test_returns_none_for_binary_file(self, tmp_path: Path) -> None:
        p = tmp_path / "binary.bin"
        p.write_bytes(b"\x00\x01\x02\xff")
        result = read_document_safe(p)
        assert result is None or isinstance(result, str)

    def test_returns_none_for_directory(self, tmp_path: Path) -> None:
        assert read_document_safe(tmp_path) is None


class TestInferDocumentType:
    def test_known_directory_names(self) -> None:
        cases = [
            ("use-cases", "use_case"),
            ("use_cases", "use_case"),
            ("business-rules", "business_rule"),
            ("business_rules", "business_rule"),
            ("actors", "actor"),
            ("processes", "process"),
            ("data", "data_group"),
            ("glossary", "term"),
            ("terms", "term"),
            ("relationships", "relationship"),
            ("sections", "section"),
        ]
        for dirname, expected in cases:
            p = Path(f"/repo/{dirname}/doc.md")
            assert infer_document_type(p) == expected

    def test_unknown_directory_falls_back(self) -> None:
        p = Path("/repo/random/dir/doc.md")
        assert infer_document_type(p) == "unknown"

    def test_root_level_file(self, tmp_path: Path) -> None:
        p = tmp_path / "doc.md"
        assert infer_document_type(p) == "unknown"


class TestMockAdapterScan:
    def test_scan_returns_documents(self, tmp_path: Path) -> None:
        (tmp_path / "specs").mkdir()
        adapter = _ValidMockAdapter()
        docs = adapter.scan(tmp_path)
        assert len(docs) == 1
        assert docs[0].id == "doc-1"
        assert docs[0].document_type == "use_case"

    def test_supported_document_types_exposed(self) -> None:
        adapter = _ValidMockAdapter()
        assert adapter.supported_document_types == ["use_case", "business_rule"]
