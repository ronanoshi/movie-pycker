"""OMDb API client (async) for metadata enrichment."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)


class OMDbClient:
    """Async client for the OMDb API (free tier)."""

    def __init__(self, api_key: str, base_url: str = "https://www.omdbapi.com/") -> None:
        self._api_key = api_key
        self._base_url = base_url

    async def fetch_movie_metadata(self, title: str) -> Dict[str, Any] | None:
        """Fetch metadata for a movie title, or return None if not found."""
        params = {"t": title, "apikey": self._api_key}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self._base_url, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
        except httpx.RequestError as exc:
            logger.warning("OMDb request failed for %s: %s", title, exc)
            return None
        except httpx.HTTPStatusError as exc:
            logger.warning("OMDb HTTP error for %s: %s", title, exc)
            return None

        if data.get("Response") != "True":
            logger.warning("OMDb no result for %s: %s", title, data.get("Error"))
            return None

        return {
            "title": data.get("Title"),
            "genres": _parse_genres(data.get("Genre")),
            "plot": data.get("Plot"),
            "runtime_minutes": _parse_runtime_minutes(data.get("Runtime"))
        }


def _parse_genres(value: str | None) -> List[str]:
    """Parse OMDb genre string into list."""
    if not value or value == "N/A":
        return []
    return [genre.strip() for genre in value.split(",") if genre.strip()]


def _parse_runtime_minutes(value: str | None) -> int | None:
    """Parse OMDb runtime string (e.g., '127 min') into integer minutes."""
    if not value or value == "N/A":
        return None
    parts = value.split()
    if not parts:
        return None
    try:
        return int(parts[0])
    except ValueError:
        return None
