from __future__ import annotations

from pathlib import Path

from specmetrics.kernel.validation.models import SpecificationDocument
from specmetrics.kernel.validation.rules.constitutional import (
    constitution_compliance_notes,
    constitution_engaged,
)


def _doc(content: str) -> SpecificationDocument:
    return SpecificationDocument(path=Path("test.md"), content=content)


class TestConstitutionEngaged:
    def test_valid_principles_passes(self):
        content = (
            "## Constitution Check\n\n"
            "**Engaged Principles**: I (Specification First), "
            "V (Evidence First), VII (Canonical Representation)\n\n"
            "**Compliance Notes**:\n- All principles addressed.\n"
        )
        result = constitution_engaged(_doc(content))
        assert result.passed

    def test_missing_engaged_principles_fails(self):
        content = "## Constitution Check\n\nNo principles listed.\n"
        result = constitution_engaged(_doc(content))
        assert not result.passed


class TestConstitutionComplianceNotes:
    def test_compliance_notes_present_passes(self):
        content = (
            "## Constitution Check\n\n"
            "**Compliance Notes**: All principles are addressed.\n"
        )
        result = constitution_compliance_notes(_doc(content))
        assert result.passed

    def test_missing_compliance_notes_fails(self):
        content = "## Constitution Check\n\n**Engaged Principles**: I (Specification First)\n"
        result = constitution_compliance_notes(_doc(content))
        assert not result.passed
