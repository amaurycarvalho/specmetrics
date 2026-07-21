from __future__ import annotations

from datetime import datetime


def generate_measure_id() -> str:
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    import uuid

    short_uuid = uuid.uuid4().hex[:8]
    return f"{timestamp}-{short_uuid}"
