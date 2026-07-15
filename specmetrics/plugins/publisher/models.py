from __future__ import annotations

from pydantic import BaseModel


class PublisherTarget(BaseModel):
    id: str
    name: str = ""
    endpoint_url: str = ""
    enabled: bool = True
    publishing_interval: int = 30
