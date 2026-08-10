"""Contribution building for Cognitive Points."""
from __future__ import annotations

import structlog

from specmetrics.kernel.token_utils import count_tokens

from .models import CognitiveContribution, EvidenceRef

logger = structlog.get_logger(__name__)


def build_contribution(
    *,
    element_id: str,
    element_type: str,
    element_name: str,
    model_source: str,
    bloom_level: str,
    cognitive_weight: float,
    content_text: str,
    content_multiplier: float,
    evidence_ref: EvidenceRef | None,
) -> CognitiveContribution:
    """Build a CognitiveContribution for a single element."""
    if not content_text:
        content_tokens = 0
        content_score = 0.0
        logger.debug("empty_content", element_id=element_id, element_type=element_type)
    else:
        content_tokens = count_tokens(content_text)
        content_score = content_tokens * content_multiplier
    partial_score = cognitive_weight + content_score
    logger.debug(
        "cognitive_contribution",
        element_id=element_id,
        element_type=element_type,
        bloom_level=bloom_level,
        content_token_count=content_tokens,
        content_score=content_score,
    )
    return CognitiveContribution(
        element_id=element_id,
        element_type=element_type,
        element_name=element_name,
        model_source=model_source,
        bloom_level=bloom_level,
        cognitive_weight=cognitive_weight,
        content_token_count=content_tokens,
        content_score=content_score,
        partial_score=partial_score,
        evidence_ref=evidence_ref,
    )