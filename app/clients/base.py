"""Base HTTP client with retry and caching."""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import Settings, get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class BaseAPIClient:
    def __init__(
        self,
        base_url: str,
        redis: Any | None = None,
        settings: Settings | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.redis = redis
        self.settings = settings or get_settings()
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._metrics: dict[str, float] = {"requests": 0, "errors": 0, "total_time": 0.0}

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={"User-Agent": "AnimeSeasonBot/1.0"},
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _cache_key(self, prefix: str, data: str) -> str:
        digest = hashlib.sha256(data.encode()).hexdigest()[:16]
        return f"cache:{prefix}:{digest}"

    async def _get_cached(self, key: str) -> Any | None:
        if not self.redis:
            return None
        raw = await self.redis.get(key)
        if raw:
            return json.loads(raw)
        return None

    async def _set_cached(self, key: str, data: Any, ttl: int | None = None) -> None:
        if not self.redis:
            return
        ttl = ttl or self.settings.cache_ttl
        await self.redis.setex(key, ttl, json.dumps(data, default=str))

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        client = await self._get_client()
        start = time.monotonic()
        self._metrics["requests"] += 1
        try:
            response = await client.request(method, path, json=json_data, params=params)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", "5"))
                logger.warning("rate_limit_hit", url=path, retry_after=retry_after)
                await self._sleep(retry_after)
                response = await client.request(method, path, json=json_data, params=params)
            response.raise_for_status()
            return response
        except Exception:
            self._metrics["errors"] += 1
            raise
        finally:
            self._metrics["total_time"] += time.monotonic() - start

    async def _sleep(self, seconds: int) -> None:
        import asyncio

        await asyncio.sleep(seconds)

    @property
    def metrics(self) -> dict[str, float]:
        return dict(self._metrics)