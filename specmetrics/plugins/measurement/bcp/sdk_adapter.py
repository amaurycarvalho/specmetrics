from __future__ import annotations

import os
import time

import structlog

from .models import SDKResult

logger = structlog.get_logger(__name__)

BCP_CLIENT = None


def _import_bcp_client():
    global BCP_CLIENT
    if BCP_CLIENT is not None:
        return BCP_CLIENT
    try:
        from bcp_calculator import BCPClient

        BCP_CLIENT = BCPClient
        return BCP_CLIENT
    except ImportError:
        pass
    try:
        from src.sdk import BCPClient

        BCP_CLIENT = BCPClient
        return BCP_CLIENT
    except ImportError:
        pass
    return None


def check_credentials(provider: str = "openai") -> str | None:
    if provider == "openai":
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            return "OPENAI_API_KEY"
    elif provider == "claude":
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            return "ANTHROPIC_API_KEY"
    return None


class BcpSdkAdapter:
    def __init__(
        self,
        provider: str = "openai",
        log_level: str = "INFO",
    ) -> None:
        self._provider = provider
        self._log_level = log_level
        self._client_class = None
        self._client = None
        self._import_error: str | None = None

        client_cls = _import_bcp_client()
        if client_cls is None:
            self._import_error = (
                "bcp-calculator SDK not installed. "
                "Install with: pip install bcp-calculator"
            )
        else:
            try:
                self._client = client_cls(provider=provider)
                self._client_class = client_cls
            except Exception as exc:
                self._import_error = str(exc)

    @property
    def is_available(self) -> bool:
        return self._client is not None and self._import_error is None

    @property
    def provider(self) -> str:
        return self._provider

    def calculate(self, story_content: str) -> SDKResult:
        if not self.is_available:
            return SDKResult(
                total_bcp=0.0,
                provider=self._provider,
                errors=[self._import_error or "SDK not available"],
            )

        missing = check_credentials(self._provider)
        if missing:
            return SDKResult(
                total_bcp=0.0,
                provider=self._provider,
                errors=[f"Missing environment variable: {missing}"],
            )

        start = time.monotonic()
        last_error: str | None = None

        for attempt in range(3):
            try:
                delay = {0: 1, 1: 2, 2: 4}[attempt]
                if attempt > 0:
                    time.sleep(delay)

                response = self._client.calculate(story_content)
                duration_ms = (time.monotonic() - start) * 1000

                if not isinstance(response, dict):
                    return SDKResult(
                        total_bcp=0.0,
                        provider=self._provider,
                        duration_ms=round(duration_ms, 2),
                        errors=["SDK returned non-dict response"],
                    )

                total_bcp = float(response.get("total_bcp", 0))
                breakdown = response.get("breakdown", {})
                if isinstance(breakdown, dict):
                    breakdown = {k: float(v) for k, v in breakdown.items()}

                return SDKResult(
                    total_bcp=total_bcp,
                    breakdown=breakdown,
                    raw_response=response,
                    provider=self._provider,
                    duration_ms=round(duration_ms, 2),
                )

            except Exception as exc:
                last_error = str(exc)
                err_str = str(exc).lower()
                if any(
                    kw in err_str
                    for kw in ["401", "403", "auth", "unauthorized", "invalid api key"]
                ):
                    duration_ms = (time.monotonic() - start) * 1000
                    return SDKResult(
                        total_bcp=0.0,
                        provider=self._provider,
                        duration_ms=round(duration_ms, 2),
                        errors=[f"Auth error: {exc}"],
                    )

                logger.debug(
                    "bcp_sdk_retry",
                    attempt=attempt + 1,
                    error=str(exc),
                )

        duration_ms = (time.monotonic() - start) * 1000
        return SDKResult(
            total_bcp=0.0,
            provider=self._provider,
            duration_ms=round(duration_ms, 2),
            errors=[f"Failed after 3 retries: {last_error}"],
        )

    def batch_calculate(self, stories: list[str]) -> list[SDKResult]:
        return [self.calculate(story) for story in stories]
