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
        content = (
            "## Constitution Check\n\n**Engaged Principles**: I (Specification First)\n"
        )
        result = constitution_compliance_notes(_doc(content))
        assert not result.passed


from specmetrics.kernel.validation.models import ValidationResult, ValidationRule
from specmetrics.kernel.validation.pipeline import ValidationPipeline


def _passing_result(name: str) -> ValidationResult:
    return ValidationResult(rule_name=name, passed=True)


def _make_rule(name: str, enabled: bool = True) -> ValidationRule:
    return ValidationRule(
        name=name, description=name, category="STRUCTURAL", enabled=enabled
    )


def _make_constitutional_rule(name: str, enabled: bool = True) -> ValidationRule:
    return ValidationRule(
        name=name, description=name, category="CONSTITUTIONAL", enabled=enabled
    )


class TestValidationPipelineCollectResults:
    def test_structural_mode_runs_structural_only(self) -> None:
        pipeline = ValidationPipeline()
        pipeline.register_rule(_make_rule("rule-a"), lambda d: _passing_result("rule-a"))
        pipeline.register_constitutional_rule(
            _make_constitutional_rule("const-a"),
            lambda d: _passing_result("const-a"),
        )
        document = _doc("content")
        results = pipeline._collect_results(document, "structural")
        names = [r.rule_name for r in results]
        assert "rule-a" in names
        assert "const-a" not in names

    def test_constitutional_mode_runs_constitutional_only(self) -> None:
        pipeline = ValidationPipeline()
        pipeline.register_rule(_make_rule("rule-a"), lambda d: _passing_result("rule-a"))
        pipeline.register_constitutional_rule(
            _make_constitutional_rule("const-a"),
            lambda d: _passing_result("const-a"),
        )
        document = _doc("content")
        results = pipeline._collect_results(document, "constitutional")
        names = [r.rule_name for r in results]
        assert "const-a" in names
        assert "rule-a" not in names

    def test_all_mode_runs_both(self) -> None:
        pipeline = ValidationPipeline()
        pipeline.register_rule(_make_rule("rule-a"), lambda d: _passing_result("rule-a"))
        pipeline.register_constitutional_rule(
            _make_constitutional_rule("const-a"),
            lambda d: _passing_result("const-a"),
        )
        document = _doc("content")
        results = pipeline._collect_results(document, "all")
        names = [r.rule_name for r in results]
        assert "rule-a" in names
        assert "const-a" in names


class TestValidationPipelineRunConstitutional:
    def test_disabled_constitutional_rule_skipped(self) -> None:
        pipeline = ValidationPipeline()
        pipeline.register_constitutional_rule(
            _make_constitutional_rule("const-a", enabled=False),
            lambda d: _passing_result("const-a"),
        )
        pipeline.register_constitutional_rule(
            _make_constitutional_rule("const-b"),
            lambda d: _passing_result("const-b"),
        )
        results = pipeline._run_constitutional(_doc("content"))
        names = [r.rule_name for r in results]
        assert "const-b" in names
        assert "const-a" not in names

    def test_registered_fn_included(self) -> None:
        pipeline = ValidationPipeline()
        pipeline.register_constitutional_rule(
            _make_constitutional_rule("const-a"),
            lambda d: _passing_result("const-a"),
        )
        results = pipeline._run_constitutional(_doc("content"))
        assert "const-a" in [r.rule_name for r in results]

    def test_missing_fn_skipped(self) -> None:
        pipeline = ValidationPipeline()
        rule = _make_constitutional_rule("const-orphan")
        pipeline._constitutional_rules.append(rule)
        results = pipeline._run_constitutional(_doc("content"))
        assert "const-orphan" not in [r.rule_name for r in results]

    def test_run_constitutional_via_validate(self, tmp_path) -> None:
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("## Constitution Check\n\nSome content here.\n")
        pipeline = ValidationPipeline()
        pipeline.register_constitutional_rule(
            _make_constitutional_rule("const-a"),
            lambda d: _passing_result("const-a"),
        )
        report = pipeline.run(spec_file, mode="constitutional")
        assert "const-a" in [r.rule_name for r in report.results]


class TestExtractPrinciples:
    def test_plain_list(self) -> None:
        from specmetrics.kernel.validation.rules.constitutional import (
            _extract_principles,
        )

        assert _extract_principles("I, II, III") == ["I", "II", "III"]

    def test_parenthesized_principles(self) -> None:
        from specmetrics.kernel.validation.rules.constitutional import (
            _extract_principles,
        )

        assert _extract_principles("(I) (Specification First)") == ["I"]

    def test_semicolon_separated(self) -> None:
        from specmetrics.kernel.validation.rules.constitutional import (
            _extract_principles,
        )

        assert _extract_principles("I; V; VII") == ["I", "V", "VII"]

    def test_invalid_tokens_excluded(self) -> None:
        from specmetrics.kernel.validation.rules.constitutional import (
            _extract_principles,
        )

        assert _extract_principles("I, XCV, II") == ["I", "II"]


class TestFindSection:
    def test_returns_section_content(self) -> None:
        from specmetrics.kernel.validation.rules.constitutional import _find_section

        content = "## Constitution Check\n\nBody line one\nBody line two\n"
        assert _find_section(content, "Constitution Check") == "\nBody line one\nBody line two"

    def test_stops_at_next_heading(self) -> None:
        from specmetrics.kernel.validation.rules.constitutional import _find_section

        content = (
            "## Constitution Check\n\nBody\n## Other Section\nOther body\n"
        )
        assert _find_section(content, "Constitution Check") == "\nBody"

    def test_non_heading_mention_ignored(self) -> None:
        from specmetrics.kernel.validation.rules.constitutional import _find_section

        content = "Intro Constitution Check\n## Constitution Check\n\nBody\n"
        assert _find_section(content, "Constitution Check") == "\nBody"

    def test_missing_section_returns_none(self) -> None:
        from specmetrics.kernel.validation.rules.constitutional import _find_section

        assert _find_section("## Other\n\nContent", "Constitution Check") is None
