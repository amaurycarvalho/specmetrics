from __future__ import annotations

from pathlib import Path

from specmetrics.kernel import _framework_packs as mod
from specmetrics.kernel._framework_packs import FrameworkPackMixin
from specmetrics.kernel.adapter_interface import Document


def _doc(document_type: str) -> Document:
    return Document(
        id="d1", path="/x/spec.md", document_type=document_type, content=""
    )


def test_detect_framework_types_detects_openspec() -> None:
    """Kills _detect_framework_types__mutmut_3 (``.lower()`` -> ``.upper()``), mutmut_4 (``or`` -> ``and``), mutmut_7/8/9 (openspec literal)."""
    mixin = FrameworkPackMixin()
    assert mixin._detect_framework_types([_doc("OpenSpec")]) == {"openspec"}


def test_detect_framework_types_detects_speckit() -> None:
    """Kills _detect_framework_types__mutmut_11/12/13 (speckit literal)."""
    mixin = FrameworkPackMixin()
    assert mixin._detect_framework_types([_doc("Speckit Story")]) == {"speckit"}


def test_detect_framework_types_detects_both() -> None:
    """Kills _detect_framework_types__mutmut_7..13 (detected.add substitutions)."""
    mixin = FrameworkPackMixin()
    detected = mixin._detect_framework_types([_doc("openspec"), _doc("feature")])
    assert detected == {"openspec", "speckit"}


def test_is_openspec_type_matches_substring_and_known_types() -> None:
    """Kills _is_openspec_type__mutmut_1 (``or`` -> ``and``), mutmut_2/3 (literal), mutmut_4 (``in`` -> ``not in`` first clause), mutmut_5 (second clause)."""
    mixin = FrameworkPackMixin()
    assert mixin._is_openspec_type("openspec") is True
    assert mixin._is_openspec_type("openspec-based") is True
    assert mixin._is_openspec_type("use_case") is True
    assert mixin._is_openspec_type("actor") is True
    assert mixin._is_openspec_type("requirement") is True
    assert mixin._is_openspec_type("unrelated") is False


def test_is_speckit_type_matches_substring_and_known_types() -> None:
    """Kills _is_speckit_type__mutmut_1 (``or`` -> ``and``), mutmut_2/3 (literal), mutmut_4 (``in`` -> ``not in`` first clause), mutmut_5 (second clause)."""
    mixin = FrameworkPackMixin()
    assert mixin._is_speckit_type("speckit") is True
    assert mixin._is_speckit_type("speckit-based") is True
    assert mixin._is_speckit_type("feature") is True
    assert mixin._is_speckit_type("scenario") is True
    assert mixin._is_speckit_type("background") is True
    assert mixin._is_speckit_type("unrelated") is False


def test_load_framework_packs_for_detected_framework() -> None:
    """Kills _load_framework_packs__mutmut_3 (rules_dir=None), mutmut_6/7 (rules literal), mutmut_9 (membership), mutmut_10/11 (path), mutmut_12 (_check_pack_version arg), mutmut_13/14 (packs.append)."""
    mixin = FrameworkPackMixin()
    mixin._detect_framework_types = lambda documents: {"openspec"}
    checked: list = []
    mixin._check_pack_version = checked.append
    expected_path = Path(mod.__file__).parent / "rules" / "openspec_rules.yaml"
    packs = mixin._load_framework_packs([_doc("openspec")])
    assert packs == [str(expected_path)]
    assert checked == [expected_path]


def test_load_framework_packs_empty_when_none_detected() -> None:
    """Kills _load_framework_packs__mutmut_9 (``framework in detected`` -> ``framework not in detected``)."""
    mixin = FrameworkPackMixin()
    mixin._detect_framework_types = lambda documents: set()
    mixin._check_pack_version = lambda path: None
    assert mixin._load_framework_packs([]) == []
