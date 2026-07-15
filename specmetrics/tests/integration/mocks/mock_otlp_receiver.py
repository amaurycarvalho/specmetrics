from __future__ import annotations

import threading
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class MockOTLPReceiver:
    def __init__(self) -> None:
        self.received_metrics: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def receive(self, metrics: list[dict[str, Any]]) -> None:
        with self._lock:
            self.received_metrics.extend(metrics)
            logger.info("mock_received_metrics", count=len(metrics))

    @property
    def metric_count(self) -> int:
        with self._lock:
            return len(self.received_metrics)

    def clear(self) -> None:
        with self._lock:
            self.received_metrics.clear()

    def get_metrics_by_name(self, name: str) -> list[dict[str, Any]]:
        with self._lock:
            return [m for m in self.received_metrics if m.get("name") == name]
