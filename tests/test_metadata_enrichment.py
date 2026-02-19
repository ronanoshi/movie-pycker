"""Tests for metadata enrichment service."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

import pytest

from app.domain.movie import MovieFile
from app.infrastructure.cache import InMemoryCache
from app.services.metadata_enrichment import (
    MetadataEnrichmentService,
    _normalize_filename
)


def _build_noise_args(noise_tokens: List[str]):
    """Convert a raw token list into the precomputed structures
    that _normalize_filename expects (compound_patterns, single_tokens)."""
    compound_patterns = [
        re.compile(r"\b" + re.escape(t) + r"\b", re.IGNORECASE)
        for t in noise_tokens if "-" in t or " " in t
    ]
    single_tokens = {
        t.lower() for t in noise_tokens if "-" not in t and " " not in t
    }
    return compound_patterns, single_tokens


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
    normalized = _normalize_filename(path, *_build_noise_args([]))

    assert normalized == "The Matrix"


def test_normalize_filename_strips_single_noise_tokens() -> None:
    path = Path("/movies/Bitter.Moon.1992.1080p.BluRay.x265.mp4")
    normalized = _normalize_filename(
        path,
        *_build_noise_args(["1080p", "BluRay", "x265"])
    )

    assert normalized == "Bitter Moon"


def test_normalize_filename_case_insensitive_matching() -> None:
    path = Path("/movies/Movie.bluray.HEVC.mkv")
    normalized = _normalize_filename(
        path,
        *_build_noise_args(["BluRay", "HEVC"])
    )

    assert normalized == "Movie"


def test_normalize_filename_strips_compound_hyphenated_token() -> None:
    path = Path("/movies/After.Hours.1985.1080p.BluRay.x265-LAMA.mp4")
    normalized = _normalize_filename(
        path,
        *_build_noise_args(["1080p", "BluRay", "x265", "LAMA"])
    )

    assert normalized == "After Hours"


def test_normalize_filename_strips_compound_before_hyphen_split() -> None:
    """Compound tokens like 'WEBRip-WORLD' are removed as a unit,
    so 'WORLD' is not left behind after hyphen splitting."""
    path = Path("/movies/A.Moment.Of.Innocence.1996.1080p.WEBRip-WORLD.mp4")
    normalized = _normalize_filename(
        path,
        *_build_noise_args(["1080p", "WEBRip", "WEBRip-WORLD"])
    )

    assert normalized == "A Moment Of Innocence"


def test_normalize_filename_preserves_world_in_title() -> None:
    """'WORLD' is not a single-word noise token, so it survives in titles."""
    path = Path("/movies/World.War.Z.2013.mkv")
    normalized = _normalize_filename(
        path,
        *_build_noise_args(["WEBRip-WORLD"])
    )

    assert normalized == "World War Z"


def test_normalize_filename_strips_brackets_and_parens() -> None:
    path = Path("/movies/Hostel[Unrated][2005]DvDrip.AC3[Eng]-aXXo.avi")
    normalized = _normalize_filename(
        path,
        *_build_noise_args(["Unrated", "DvDrip", "AC3", "Eng", "aXXo"])
    )

    assert normalized == "Hostel"


def test_normalize_filename_strips_compound_space_token() -> None:
    """Compound tokens with spaces (e.g. 'Ac3 SNAKE') are removed as phrases."""
    path = Path("/movies/Glory Daze 1995 DVDRip X264 Ac3 SNAKE.mkv")
    normalized = _normalize_filename(
        path,
        *_build_noise_args(["DVDRip", "X264", "Ac3 SNAKE"])
    )

    assert normalized == "Glory Daze"


def test_normalize_filename_empty_noise_tokens() -> None:
    path = Path("/movies/Cargo.2009.1080p.BluRay.AV1.mkv")
    normalized = _normalize_filename(path, *_build_noise_args([]))

    assert normalized == "Cargo 1080p BluRay AV1"
