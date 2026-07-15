from __future__ import annotations

from typing import Optional

from .models import ComplexityRating, FunctionType

DET_RET_MATRIX: list[tuple[int, int, ComplexityRating]] = [
    (1, 19, "Low"),
    (20, 50, "Low"),
    (51, -1, "Average"),
    (1, 19, "Low"),
    (20, 50, "Average"),
    (51, -1, "High"),
    (1, 19, "Average"),
    (20, 50, "High"),
    (51, -1, "High"),
]

RET_BOUNDARIES: list[int] = [1, 2, 6]
DET_BOUNDARIES_DATA: list[int] = [19, 50]

UFP_WEIGHTS: dict[FunctionType, dict[ComplexityRating, int]] = {
    "ILF": {"Low": 7, "Average": 10, "High": 15},
    "EIF": {"Low": 5, "Average": 7, "High": 10},
    "EI": {"Low": 3, "Average": 4, "High": 6},
    "EO": {"Low": 4, "Average": 5, "High": 7},
    "EQ": {"Low": 3, "Average": 4, "High": 6},
}

TRANSACTIONAL_MATRICES: dict[FunctionType, dict[str, list[int]]] = {
    "EI": {
        "ftr_boundaries": [0, 2, 3],
        "det_boundaries": [4, 15],
    },
    "EO": {
        "ftr_boundaries": [0, 2, 4],
        "det_boundaries": [5, 19],
    },
    "EQ": {
        "ftr_boundaries": [0, 2, 4],
        "det_boundaries": [5, 19],
    },
}

TRANSACTIONAL_LOOKUP: dict[str, list[list[ComplexityRating]]] = {
    "EI": [
        ["Low", "Low", "Average"],
        ["Low", "Average", "High"],
        ["Average", "High", "High"],
    ],
    "EO": [
        ["Low", "Low", "Average"],
        ["Low", "Average", "High"],
        ["Average", "High", "High"],
    ],
    "EQ": [
        ["Low", "Low", "Average"],
        ["Low", "Average", "High"],
        ["Average", "High", "High"],
    ],
}


def _get_ret_index(ret: int, boundaries: list[int] | None = None) -> int:
    b = boundaries or RET_BOUNDARIES
    if ret <= b[0]:
        return 0
    if ret <= b[1]:
        return 1
    return 2


def _get_det_index(det: int, boundaries: list[int]) -> int:
    if det <= boundaries[0]:
        return 0
    if det <= boundaries[1]:
        return 1
    return 2


def classify_data_function_complexity(
    ret_count: int,
    det_count: int,
    ret_boundaries: Optional[list[int]] = None,
    det_boundaries: Optional[list[int]] = None,
) -> ComplexityRating:
    rb = ret_boundaries or RET_BOUNDARIES
    db = det_boundaries or DET_BOUNDARIES_DATA
    ret_idx = _get_ret_index(ret_count, rb)
    det_idx = _get_det_index(det_count, db)
    matrix: list[list[ComplexityRating]] = [
        ["Low", "Low", "Average"],
        ["Low", "Average", "High"],
        ["Average", "High", "High"],
    ]
    return matrix[ret_idx][det_idx]


def classify_transactional_complexity(
    function_type: FunctionType,
    ftr_count: int,
    det_count: int,
    ftr_boundaries: Optional[list[int]] = None,
    det_boundaries: Optional[list[int]] = None,
) -> ComplexityRating:
    config = TRANSACTIONAL_MATRICES[function_type]
    fb = ftr_boundaries or config["ftr_boundaries"]
    db = det_boundaries or config["det_boundaries"]
    ftr_idx = _get_ret_index(ftr_count, fb)
    det_idx = _get_det_index(det_count, db)
    return TRANSACTIONAL_LOOKUP[function_type][ftr_idx][det_idx]


def get_ufp_weight(
    function_type: FunctionType,
    complexity: ComplexityRating,
    weight_overrides: Optional[dict[str, dict[str, int]]] = None,
) -> int:
    table = weight_overrides or UFP_WEIGHTS
    return table[function_type][complexity]
