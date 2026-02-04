"""Tests for the movies API endpoints."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.api.movies import get_cache
from app.domain.movie import MovieMetadata
from app.infrastructure.cache import InMemoryCache
from app.main import app


def _movie(title: str, duration: int, file_name: str) -> MovieMetadata:
    return MovieMetadata(
        file_path=Path(f"/movies/{file_name}"),
        title=title,
        duration_minutes=duration,
    )


def test_list_movies_default_sort() -> None:
    movie_a = _movie("A", 100, "a.mp4")
    movie_b = _movie("B", 120, "b.mp4")
    cache = InMemoryCache(
        {
            str(movie_a.file_path): movie_a,
            str(movie_b.file_path): movie_b,
        }
    )

    app.dependency_overrides[get_cache] = lambda: cache
    client = TestClient(app)

    try:
        response = client.get("/movies")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    durations = [movie["duration_minutes"] for movie in payload["results"]]
    assert durations == [100, 120]


def test_list_movies_sort_descending() -> None:
    movie_a = _movie("A", 100, "a.mp4")
    movie_b = _movie("B", 120, "b.mp4")
    cache = InMemoryCache(
        {
            str(movie_a.file_path): movie_a,
            str(movie_b.file_path): movie_b,
        }
    )

    app.dependency_overrides[get_cache] = lambda: cache
    client = TestClient(app)

    try:
        response = client.get("/movies?sort=-duration")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    durations = [movie["duration_minutes"] for movie in payload["results"]]
    assert durations == [120, 100]

