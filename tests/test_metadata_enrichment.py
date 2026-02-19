"""Tests for metadata enrichment service."""

from __future__ import annotations

from pathlib import Path
from typing import List

import pytest

from app.domain.movie import MovieFile
from app.infrastructure.cache import InMemoryCache
from app.services.metadata_enrichment import (
    MetadataEnrichmentService,
    _normalize_filename
)


class _FakeOmdbClient:
    """Fake OMDb client for tests."""

    def __init__(self, response: dict | None) -> None:
        self.response = response
        self.calls: List[str] = []

    async def fetch_movie_metadata(self, title: str) -> dict | None:
        self.calls.append(title)
        return self.response


@pytest.mark.asyncio
async def test_enrich_movies_uses_cache() -> None:
    cache = InMemoryCache()
    client = _FakeOmdbClient(
        response={
            "title": "Cached",
            "genres": [],
            "plot": None,
            "runtime_minutes": None
        }
    )
    service = MetadataEnrichmentService(client, cache)

    movie = MovieFile(
        file_path=Path("/movies/cached.mp4"),
        filename="cached.mp4",
        duration_minutes=100
    )
    cached_metadata = await service.enrich_movies([movie])

    # Second call should hit cache and avoid OMDb call.
    cached_again = await service.enrich_movies([movie])

    assert cached_metadata == cached_again
    assert client.calls == ["cached"]


@pytest.mark.asyncio
async def test_enrich_movies_missing_omdb() -> None:
    cache = InMemoryCache()
    client = _FakeOmdbClient(response=None)
    service = MetadataEnrichmentService(client, cache)

    movie = MovieFile(
        file_path=Path("/movies/unknown.mkv"),
        filename="unknown.mkv",
        duration_minutes=95
    )
    results = await service.enrich_movies([movie])

    assert results[0].title is None
    assert results[0].genres == []
    assert results[0].plot is None
    assert results[0].duration_minutes == 95


@pytest.mark.asyncio
async def test_enrich_movies_uses_runtime_when_duration_missing() -> None:
    cache = InMemoryCache()
    client = _FakeOmdbClient(
        response={
            "title": "Short",
            "genres": ["Drama"],
            "plot": "Test",
            "runtime_minutes": 80
        }
    )
    service = MetadataEnrichmentService(client, cache)

    movie = MovieFile(
        file_path=Path("/movies/short.avi"),
        filename="short.avi",
        duration_minutes=0
    )
    results = await service.enrich_movies([movie])

    assert results[0].duration_minutes == 80


def test_normalize_filename_removes_year_and_separators() -> None:
    path = Path("/movies/The.Matrix.1999.mkv")
    normalized = _normalize_filename(path)

    assert normalized == "The Matrix"
