from __future__ import annotations

import re
from typing import Optional

from specmetrics.kernel.evidence_graph import GraphNode


FRAMEWORK_PATTERNS = [
    re.compile(r"^(?:OpenSpec|SpecKit|SpecMetrics)\s+(?:Section|Document|Measurement|Feature|Element|Concept):\s*", re.IGNORECASE),
    re.compile(r"^(?:open_spec|speckit|specmetrics)[_.].*", re.IGNORECASE),
]

ACTOR_PATTERNS = re.compile(
    r"^(admin|administrator|user|manager|operator|developer|analyst|viewer|editor|"
    r"owner|contributor|reviewer|approver|customer|client|agent|bot|service|"
    r"system|coordinator|supervisor|lead|member|participant)$",
    re.IGNORECASE,
)


def classify_node(node: GraphNode) -> Optional[str]:
    if node.node_type != "extracted_element":
        return None
    semantic_type = node.semantic_type
    if semantic_type == "fact":
        return "business_rule"
    elif semantic_type == "entity":
        return _classify_entity(node)
    elif semantic_type == "relationship":
        return "relationship"
    elif semantic_type == "operation":
        return "operation"
    return None


def _classify_entity(node: GraphNode) -> str:
    name = node.text.strip()
    if ACTOR_PATTERNS.match(name):
        return "actor"
    if name[0].isupper() and _is_data_like(name):
        return "data_group"
    if _is_role_suffix(name):
        return "actor"
    return "data_group"


def _is_data_like(name: str) -> bool:
    data_patterns = re.compile(
        r"(Account|Record|Data|Info|Log|Report|Config|Settings|Profile|"
        r"Document|File|Table|List|Queue|Cache|Session|Token|Key)$",
        re.IGNORECASE,
    )
    return bool(data_patterns.search(name))


def _is_role_suffix(name: str) -> bool:
    return bool(re.search(r"(er|or|ant|ent|ist|ian|eer)$", name, re.IGNORECASE))


def strip_framework_labels(text: str) -> str:
    for pattern in FRAMEWORK_PATTERNS:
        text = pattern.sub("", text)
    return text.strip()
