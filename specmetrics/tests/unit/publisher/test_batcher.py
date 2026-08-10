from __future__ import annotations

import time
from typing import Any

from specmetrics.plugins.publisher.base import PublisherConfiguration
from specmetrics.plugins.publisher.batcher import MetricBatcher


class TestMetricBatcher:
    def test_enqueue_single(self) -> None:
        config = PublisherConfiguration(
            endpoint_url="http://localhost:4318",
            batch_interval_seconds=60,
            batch_max_size=100,
        )
        exported: list[list[dict[str, Any]]] = []

        def export_fn(batch: list[dict[str, Any]]) -> None:
            exported.append(batch)

        batcher = MetricBatcher(config, export_fn)
        batcher.start()
        batcher.enqueue({"name": "test.metric", "value": 1.0})
        time.sleep(0.1)
        batcher.stop()

        assert batcher.get_status()["queue_depth"] == 0

    def test_batch_on_size(self) -> None:
        config = PublisherConfiguration(
            endpoint_url="http://localhost:4318",
            batch_interval_seconds=60,
            batch_max_size=3,
        )
        exported: list[list[dict[str, Any]]] = []

        def export_fn(batch: list[dict[str, Any]]) -> None:
            exported.append(batch)

        batcher = MetricBatcher(config, export_fn)
        batcher.start()

        batcher.enqueue({"name": "m1", "value": 1.0})
        batcher.enqueue({"name": "m2", "value": 2.0})
        batcher.enqueue({"name": "m3", "value": 3.0})  # should trigger flush

        time.sleep(0.1)
        batcher.stop()

        assert len(exported) >= 1
        if exported:
            assert len(exported[0]) == 3

    def test_queue_overflow(self) -> None:
        config = PublisherConfiguration(
            endpoint_url="http://localhost:4318",
            queue_max_size=2,
            batch_interval_seconds=60,
            batch_max_size=10,
        )
        exported: list[list[dict[str, Any]]] = []

        def export_fn(batch: list[dict[str, Any]]) -> None:
            exported.append(batch)

        batcher = MetricBatcher(config, export_fn)
        batcher.start()
        batcher.enqueue({"name": "m1", "value": 1.0})
        batcher.enqueue({"name": "m2", "value": 2.0})
        batcher.enqueue({"name": "m3", "value": 3.0})  # should drop m1
        time.sleep(0.1)
        batcher.stop()

        assert batcher.get_status()["queue_depth"] == 0
