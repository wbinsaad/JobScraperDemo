# jobflow_engine/jobs_client.py

import asyncio
from typing import Any

import httpx

from config import settings
from logger import get_logger
from models import JobSource


logger = get_logger(__name__)


class JobFetchError(Exception):
    """Raised when a job source cannot be fetched."""


class JobsClient:
    """
    Generic HTTP client for fetching jobs from configured job sources.
    """
    
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or settings.jobs_api_url).rstrip("/")

    async def fetch_source(
        self,
        source: JobSource,
        client: httpx.AsyncClient,
    ) -> list[dict[str, Any]]:
        """
        Fetch jobs from a single configured source.

        Args:
            source: JobSource configuration loaded from DB.
            client: Shared AsyncClient for connection reuse.

        Returns:
            List of raw job dictionaries.
        """
        endpoint_path = self._normalise_endpoint_path(source.endpoint_path)
        url = f"{self.base_url}{endpoint_path}"

        logger.info(
            "Fetching jobs from source | source=%s | url=%s",
            source.name,
            url,
        )

        try:
            response = await client.get(url, timeout=source.timeout_seconds)
            response.raise_for_status()

        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Job source returned bad HTTP status | source=%s | status_code=%s",
                source.name,
                exc.response.status_code,
            )
            raise JobFetchError(
                f"Source '{source.name}' returned HTTP {exc.response.status_code}"
            ) from exc

        except httpx.RequestError as exc:
            logger.warning(
                "Failed to call job source | source=%s | error=%s",
                source.name,
                str(exc),
            )
            raise JobFetchError(f"Failed to call source '{source.name}'") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            logger.warning(
                "Job source returned invalid JSON | source=%s",
                source.name,
            )
            raise JobFetchError(f"Source '{source.name}' returned invalid JSON") from exc

        if not isinstance(payload, list):
            logger.warning(
                "Job source returned unexpected payload type | source=%s | actual_type=%s",
                source.name,
                type(payload).__name__,
            )
            raise JobFetchError(
                f"Source '{source.name}' returned unexpected payload format"
            )

        logger.info(
            "Fetched jobs from source | source=%s | count=%s",
            source.name,
            len(payload),
        )

        return payload

    async def fetch_all_sources(
        self,
        sources: list[JobSource],
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Fetch jobs from all enabled sources concurrently.

        Returns:
            {
                "linkedin": [...],
                "seek": [...]
            }
        """
        enabled_sources = [source for source in sources if source.enabled]

        logger.info(
            "Fetching all enabled job sources | enabled_source_count=%s",
            len(enabled_sources),
        )

        results: dict[str, list[dict[str, Any]]] = {}

        async with httpx.AsyncClient() as client:
            tasks = [
                self._safe_fetch_source(source=source, client=client)
                for source in enabled_sources
            ]

            source_results = await asyncio.gather(*tasks)

        for source_name, jobs in source_results:
            results[source_name] = jobs

        total_jobs = sum(len(jobs) for jobs in results.values())

        logger.info(
            "Finished fetching all sources | source_count=%s | total_jobs=%s",
            len(results),
            total_jobs,
        )

        return results

    async def _safe_fetch_source(
        self,
        source: JobSource,
        client: httpx.AsyncClient,
    ) -> tuple[str, list[dict[str, Any]]]:
        """
        Fetch a source without allowing one failed source to stop all others.
        """
        try:
            jobs = await self.fetch_source(source=source, client=client)
            return source.name, jobs

        except JobFetchError as exc:
            logger.warning(
                "Skipping failed job source | source=%s | error=%s",
                source.name,
                str(exc),
            )
            return source.name, []

    @staticmethod
    def _normalise_endpoint_path(endpoint_path: str) -> str:
        """
        Ensure endpoint path starts with a single slash.
        """
        return "/" + endpoint_path.strip("/")