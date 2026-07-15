from __future__ import annotations

import time
from collections import deque
from threading import Lock, Timer
from typing import Any, Callable

import structlog

from .base import PublisherConfiguration

logger = structlog.get_logger(__name__)


class MetricBatcher:
    def __init__(
        self,
        config: PublisherConfiguration,
        export_fn: Callable[[list[dict[str, Any]]], None],
    ) -> None:
        self.config = config
        self.export_fn = export_fn
        self.queue: deque[dict[str, Any]] = deque(maxlen=config.queue_max_size)
        self.lock = Lock()
        self._timer: Timer | None = None
        self._running = False
        self._total_exported = 0
        self._consecutive_errors = 0
        self._last_error: str | None = None
        self._started_at: float = 0.0

    def start(self) -> None:
        self._running = True
        self._started_at = time.time()
        self._schedule_flush()

    def stop(self) -> None:
        if self._timer:
            self._timer.cancel()
        self._flush()
        with self.lock:
            self._running = False

    def enqueue(self, metric: dict[str, Any]) -> int:
        with self.lock:
            if len(self.queue) >= self.config.queue_max_size:
                dropped = self.queue.popleft()
                logger.warning(
                    "metric_queue_overflow",
                    dropped_metric=dropped.get("name"),
                    queue_size=len(self.queue),
                )
            self.queue.append(metric)
            current_size = len(self.queue)
            if current_size >= self.config.batch_max_size:
                self._flush()
        return current_size

    def get_status(self) -> dict[str, Any]:
        uptime = time.time() - self._started_at if self._started_at else 0.0
        return {
            "total_exported": self._total_exported,
            "consecutive_errors": self._consecutive_errors,
            "queue_depth": len(self.queue),
            "last_error": self._last_error,
            "uptime_seconds": uptime,
            "running": self._running,
        }

    def _schedule_flush(self) -> None:
        with self.lock:
            if not self._running:
                return
        self._timer = Timer(self.config.batch_interval_seconds, self._flush)
        self._timer.daemon = True
        self._timer.start()

    def _flush(self) -> None:
        with self.lock:
            batch = list(self.queue)
            self.queue.clear()

        if not batch:
            self._schedule_flush()
            return

        try:
            self.export_fn(batch)
            self._total_exported += len(batch)
            self._consecutive_errors = 0
            self._last_error = None
        except Exception as exc:
            self._consecutive_errors += 1
            self._last_error = str(exc)
            logger.error(
                "batch_export_failed",
                error=str(exc),
                consecutive_errors=self._consecutive_errors,
            )
            if self._consecutive_errors >= self.config.retry_max_attempts:
                logger.warning("batch_discarded_after_max_retries", metrics=len(batch))
                self._consecutive_errors = 0
                self._last_error = None

        self._schedule_flush()
