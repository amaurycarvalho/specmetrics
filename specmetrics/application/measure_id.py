"""Generation of unique measurement identifiers."""

from __future__ import annotations

from datetime import UTC, datetime


def generate_measure_id() -> str:
    """Generate a unique measure identifier based on timestamp and a short UUID."""
    now = datetime.now(UTC)
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    import uuid

    short_uuid = uuid.uuid4().hex[:8]
    return f"{timestamp}-{short_uuid}"
