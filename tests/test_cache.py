"""Tests for cache interface and in-memory implementation."""

from pathlib import Path

from app.domain.movie import MovieMetadata
from app.infrastructure.cache import InMemoryCache


def _sample_movie(title: str, duration: int) -> MovieMetadata:
    """Create a sample MovieMetadata instance for tests."""
    return MovieMetadata(
        file_path=Path(f"/movies/{title.lower().replace(' ', '_')}.mp4"),
        title=title,
        genres=["Action"],
        plot=f"{title} plot",
        duration_minutes=duration,
    )


def test_cache_set_and_get() -> None:
    """Test that values can be stored and retrieved."""
    cache = InMemoryCache()
    key = "movie:1"
    movie = _sample_movie("Test Movie", 120)

    cache.set(key, movie)

    assert cache.get(key) == movie


def test_cache_exists() -> None:
    """Test that exists() reflects cache contents."""
    cache = InMemoryCache()
    key = "movie:1"
    movie = _sample_movie("Test Movie", 120)

    assert cache.exists(key) is False

    cache.set(key, movie)

    assert cache.exists(key) is True


def test_cache_clear() -> None:
    """Test that clear() removes all items."""
    cache = InMemoryCache()
    cache.set("movie:1", _sample_movie("Movie 1", 100))
    cache.set("movie:2", _sample_movie("Movie 2", 110))

    assert len(cache.get_all()) == 2

    cache.clear()

    assert cache.get_all() == {}


def test_cache_get_all_returns_copy() -> None:
    """Test that get_all returns a copy, not the internal dict."""
    movie = _sample_movie("Test Movie", 120)
    cache = InMemoryCache({"movie:1": movie})

    all_items = cache.get_all()
    all_items["movie:2"] = _sample_movie("Movie 2", 130)

    # Internal cache should not be affected by external modifications.
    assert cache.exists("movie:2") is False
    assert cache.get("movie:1") == movie


def test_cache_initial_data_is_copied() -> None:
    """Test that initial data is copied to avoid shared references."""
    movie = _sample_movie("Test Movie", 120)
    initial = {"movie:1": movie}

    cache = InMemoryCache(initial)
    initial["movie:2"] = _sample_movie("Movie 2", 130)

    assert cache.exists("movie:2") is False


