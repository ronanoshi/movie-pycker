"""Metadata enrichment service using OMDb with caching."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Iterable, List

from app.domain.movie import MovieFile, MovieMetadata
from app.infrastructure.cache import Cache
from app.infrastructure.omdb_client import OMDbClient

logger = logging.getLogger(__name__)

_YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")


class MetadataEnrichmentService:
    """Enriches movies using OMDb and caches the results."""

    def __init__(self, omdb_client: OMDbClient, cache: Cache) -> None:
        self._omdb_client = omdb_client
        self._cache = cache

    async def enrich_movies(self, movies: Iterable[MovieFile]) -> List[MovieMetadata]:
        """Enrich a list of MovieFile objects with OMDb metadata."""
        enriched: List[MovieMetadata] = []

        for movie in movies:
            cache_key = str(movie.file_path)
            cached = self._cache.get(cache_key)
            if cached:
                enriched.append(cached)
                continue

            title_query = _normalize_filename(movie.file_path)
            omdb_data = await self._omdb_client.fetch_movie_metadata(title_query)

            metadata = _build_metadata(movie, omdb_data)
            self._cache.set(cache_key, metadata)
            enriched.append(metadata)

        return enriched


def _normalize_filename(file_path: Path) -> str:
    """Normalize filename for OMDb lookup."""
    name = file_path.stem
    name = name.replace(".", " ").replace("_", " ")
    name = _YEAR_PATTERN.sub("", name)
    name = " ".join(name.split())
    return name.strip()


def _build_metadata(movie: MovieFile, omdb_data: dict | None) -> MovieMetadata:
    """Create MovieMetadata from MovieFile and optional OMDb data."""
    if not omdb_data:
        return MovieMetadata(
            file_path=movie.file_path,
            title=None,
            genres=[],
            plot=None,
            duration_minutes=movie.duration_minutes,
        )

    duration_minutes = movie.duration_minutes
    runtime_minutes = omdb_data.get("runtime_minutes")
    if duration_minutes == 0 and isinstance(runtime_minutes, int):
        duration_minutes = runtime_minutes

    return MovieMetadata(
        file_path=movie.file_path,
        title=omdb_data.get("title"),
        genres=omdb_data.get("genres", []),
        plot=omdb_data.get("plot"),
        duration_minutes=duration_minutes,
    )


