from __future__ import annotations

import json
from pathlib import Path


def load_cfm(run_dir: Path):
    cfm_path = run_dir / "canonical_model.json"
    if not cfm_path.exists():
        return None
    from specmetrics.kernel.cfm.model import CanonicalFunctionalModel

    with open(cfm_path) as f:
        data = json.load(f)
    return CanonicalFunctionalModel.model_validate(data)


def load_evidence_graph(run_dir: Path):
    graph_path = run_dir / "evidence_graph.json"
    if not graph_path.exists():
        return None
    from specmetrics.kernel.evidence_graph import EvidenceGraph

    with open(graph_path) as f:
        data = json.load(f)
    return EvidenceGraph.model_validate(data)
