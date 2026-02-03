"""Tests for search service."""

from pathlib import Path

from app.domain.movie import MovieMetadata
from app.services.search import SearchService


def _movie(
    title: str,
    genres: list[str],
    plot: str,
    duration: int,
) -> MovieMetadata:
    return MovieMetadata(
        file_path=Path(f"/movies/{title.lower().replace(' ', '_')}.mp4"),
        title=title,
        genres=genres,
        plot=plot,
        duration_minutes=duration,
    )


def test_search_returns_all_when_no_keywords() -> None:
    service = SearchService()
    movies = [
        _movie("Se7en", ["Crime", "Thriller"], "Detective story", 127),
        _movie("Toy Story", ["Animation"], "Toys come alive", 81),
    ]

    results = service.search(movies, keywords=[], sort="duration")

    assert results == sorted(movies, key=lambda m: m.duration_minutes)


def test_search_matches_title_plot_genres() -> None:
    service = SearchService()
    movies = [
        _movie("Se7en", ["Crime", "Thriller"], "Detective story", 127),
        _movie("Toy Story", ["Animation"], "Toys come alive", 81),
        _movie("The Dark Knight", ["Action"], "Dark hero", 152),
    ]

    results = service.search(movies, keywords=["dark", "thriller"], sort="duration")

    titles = [movie.title for movie in results]
    assert "The Dark Knight" in titles
    assert "Se7en" in titles
    assert "Toy Story" not in titles


def test_search_sort_descending() -> None:
    service = SearchService()
    movies = [
        _movie("A", ["Drama"], "Plot", 100),
        _movie("B", ["Drama"], "Plot", 200),
    ]

    results = service.search(movies, keywords=[], sort="-duration")

    assert [movie.duration_minutes for movie in results] == [200, 100]


def test_search_unknown_sort_is_stable() -> None:
    service = SearchService()
    movies = [
        _movie("A", ["Drama"], "Plot", 100),
        _movie("B", ["Drama"], "Plot", 200),
    ]

    results = service.search(movies, keywords=[], sort="unknown")

    # Unknown sort keeps original order
    assert results == movies


