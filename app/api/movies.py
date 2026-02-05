"""Movies API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from app.domain.movie import SearchResponse
from app.infrastructure.cache import InMemoryCache
from app.services.search import SearchService

router = APIRouter(prefix="/movies", tags=["movies"])

_search_service = SearchService()


def get_cache(request: Request) -> InMemoryCache:
    """Provide a shared cache instance for the API."""
    cache = getattr(request.app.state, "cache", None)
    if cache is None:
        cache = InMemoryCache()
        request.app.state.cache = cache
    return cache


def get_search_service() -> SearchService:
    """Provide a shared search service instance for the API."""
    return _search_service


@router.get("", response_model=SearchResponse)
def list_movies(
    request: Request,
    sort: str = Query(
        default="duration",
        description="Sort field (e.g., 'duration' or '-duration')",
    ),
    cache: InMemoryCache = Depends(get_cache),
    search_service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    """Return all cached movies sorted by the requested field."""
    movies = list(cache.get_all().values())
    results = search_service.search(movies, keywords=[], sort=sort)
    return SearchResponse(results=results)

