"""Metadata enrichment service using OMDb with caching."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Iterable, List, Set

from app.domain.movie import MovieFile, MovieMetadata
from app.infrastructure.cache import Cache
from app.infrastructure.omdb_client import OMDbClient

logger = logging.getLogger(__name__)

_YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")


class MetadataEnrichmentService:
    """Enriches movies using OMDb and caches the results."""

    def __init__(
        self,
        omdb_client: OMDbClient,
        cache: Cache,
        noise_tokens: List[str] | None = None
    ) -> None:
        self._omdb_client = omdb_client
        self._cache = cache
        tokens = noise_tokens or []
        self._compound_patterns = [
            re.compile(r"\b" + re.escape(t) + r"\b", re.IGNORECASE)
            for t in tokens if "-" in t or " " in t
        ]
        self._single_tokens = {
            t.lower() for t in tokens if "-" not in t and " " not in t
        }

    async def enrich_movies(self, movies: Iterable[MovieFile]) -> List[MovieMetadata]:
        """Enrich a list of MovieFile objects with OMDb metadata."""
        enriched: List[MovieMetadata] = []

        for movie in movies:
            cache_key = str(movie.file_path)
            cached = self._cache.get(cache_key)
            if cached:
                enriched.append(cached)
                continue

            title_query = _normalize_filename(
                movie.file_path,
                self._compound_patterns,
                self._single_tokens
            )
            omdb_data = await self._omdb_client.fetch_movie_metadata(title_query)

            metadata = _build_metadata(movie, omdb_data)
            self._cache.set(cache_key, metadata)
            enriched.append(metadata)

        return enriched


def _normalize_filename(
    file_path: Path,
    compound_patterns: List[re.Pattern[str]],
    single_tokens: Set[str]
) -> str:
    """Normalize filename for OMDb lookup.

    Strips the extension, replaces common separators with spaces, removes
    year patterns, then removes configurable noise tokens.  Compound patterns
    (precompiled regexes with word boundaries) are applied *before* hyphens
    are replaced, so ``WEBRip-WORLD`` is removed as a unit.  Single-word
    tokens are filtered afterwards via a fast set-lookup.
    """
    name = file_path.stem

    for char in "._()[]":
        name = name.replace(char, " ")

    name = _YEAR_PATTERN.sub("", name)

    for pattern in compound_patterns:
        name = pattern.sub("", name)

    name = name.replace("-", " ")

    words = name.split()
    words = [w for w in words if w.lower() not in single_tokens]

    return " ".join(words).strip()


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
