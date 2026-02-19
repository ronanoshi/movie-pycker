"""Search service for filtering and sorting movies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List

from app.domain.movie import MovieMetadata


@dataclass(frozen=True)
class SearchCriteria:
    """Search criteria for filtering and sorting."""

    keywords: List[str]
    sort: str


class SearchService:
    """Filter and sort movies based on keywords and sort fields."""

    def search(
        self,
        movies: Iterable[MovieMetadata],
        keywords: List[str],
        sort: str,
    ) -> List[MovieMetadata]:
        criteria = SearchCriteria(keywords=keywords, sort=sort)
        filtered = self._filter_movies(movies, criteria.keywords)
        return self._sort_movies(filtered, criteria.sort)

    def _filter_movies(
        self,
        movies: Iterable[MovieMetadata],
        keywords: List[str],
    ) -> List[MovieMetadata]:
        if not keywords:
            return list(movies)

        normalized = [kw.lower().strip() for kw in keywords if kw.strip()]
        if not normalized:
            return list(movies)

        results: List[MovieMetadata] = []
        for movie in movies:
            if _matches_keywords(movie, normalized):
                results.append(movie)
        return results

    def _sort_movies(self, movies: List[MovieMetadata], sort: str) -> List[MovieMetadata]:
        key, reverse = _parse_sort(sort)
        return sorted(movies, key=key, reverse=reverse)


def _matches_keywords(movie: MovieMetadata, keywords: List[str]) -> bool:
    """Return True if any keyword matches title, plot, or genres."""
    haystack = " ".join(
        [
            (movie.title or ""),
            (movie.plot or ""),
            " ".join(movie.genres)
        ]
    ).lower()
    return any(keyword in haystack for keyword in keywords)


def _parse_sort(sort: str) -> tuple[Callable[[MovieMetadata], int], bool]:
    """Parse sort string into key function and reverse flag."""
    if sort.startswith("-"):
        field = sort[1:]
        reverse = True
    else:
        field = sort
        reverse = False

    if field == "duration":
        return (lambda movie: movie.duration_minutes), reverse

    # Default: no-op sort (stable) if unknown field
    return (lambda _movie: 0), False
