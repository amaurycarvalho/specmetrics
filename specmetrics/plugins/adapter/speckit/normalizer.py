"""Normalize SpecKit specification files into canonical documents."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from specmetrics.kernel.adapter_interface import Document, DocumentSection

from .metadata import ARTIFACT_TYPE_MAP, build_metadata

ATX_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)(?:\s+#+\s*)?$", re.MULTILINE)


def _parse_sections(content: str) -> list[DocumentSection]:
    if not content.strip():
        return []

    sections: list[dict[str, Any]] = []
    lines = content.split("\n")
    current_section: dict[str, Any] | None = None
    section_counter = 0

    for line in lines:
        m = ATX_HEADING_RE.match(line)
        if m:
            section_counter += 1
            level = len(m.group(1))
            title = m.group(2).strip()
            sec = DocumentSection(
                id=f"sec-{section_counter}",
                title=title,
                level=level,
                content="",
                subsections=[] if level < 6 else None,
            )
            if current_section is not None:
                _attach_section(sections, current_section)
            current_section = {"section": sec, "body_lines": [], "level": level}
        else:
            if current_section is not None:
                current_section["body_lines"].append(line)

    if current_section is not None:
        _attach_section(sections, current_section)

    return _build_hierarchy(sections)


def _attach_section(sections: list[dict[str, Any]], current: dict[str, Any]) -> None:
    sec = current["section"]
    body = "\n".join(current["body_lines"]).strip()
    sections.append({"section": sec, "body": body, "level": current["level"]})


def _build_hierarchy(flat: list[dict[str, Any]]) -> list[DocumentSection]:
    root: list[DocumentSection] = []
    stack: list[tuple[int, DocumentSection]] = []

    for item in flat:
        body = item["body"]
        level = item["level"]

        normalized = DocumentSection(
            id=item["section"].id,
            title=item["section"].title,
            level=level,
            content=body,
            subsections=[],
        )

        while stack and stack[-1][0] >= level:
            stack.pop()

        if stack:
            stack[-1][1].subsections.append(normalized)
        else:
            root.append(normalized)

        stack.append((level, normalized))

    return root


def _infer_document_type(file_path: Path) -> str:
    name = file_path.name
    if "checklists" in file_path.parts:
        return "checklist"
    return ARTIFACT_TYPE_MAP.get(name, "unknown")


def _make_document_id(file_path: Path, repo_root: Path) -> str:
    try:
        relative = file_path.relative_to(repo_root)
    except ValueError:
        relative = file_path
    artifact_type = _infer_document_type(file_path)
    return f"speckit:{artifact_type}:{relative}"


def normalize_document(file_path: Path, repo_root: Path) -> Document:
    """Normalize a SpecKit file into a canonical document."""
    content = file_path.read_text(encoding="utf-8")
    sections = _parse_sections(content)
    metadata = build_metadata(file_path, repo_root)
    document_type = _infer_document_type(file_path)
    doc_id = _make_document_id(file_path, repo_root)

    try:
        relative_path = str(file_path.relative_to(repo_root))
    except ValueError:
        relative_path = str(file_path)

    return Document(
        id=doc_id,
        path=relative_path,
        document_type=document_type,
        content=content,
        metadata=metadata,
        sections=sections,
    )
