"""Movies API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.core.config import get_settings
from app.domain.movie import SearchResponse
from app.infrastructure.cache import InMemoryCache
from app.services.library_loader import load_library
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
async def list_movies(
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
    settings = getattr(request.app.state, "settings", None)
    if settings is None and movies:
        results = search_service.search(movies, keywords=[], sort=sort)
        return SearchResponse(results=results)

    if settings is None:
        settings = get_settings()
        request.app.state.settings = settings

    if not settings.enable_cache:
        temp_cache = InMemoryCache()
        movies = await load_library(settings, temp_cache)
        results = search_service.search(movies, keywords=[], sort=sort)
        return SearchResponse(results=results)

    if not movies:
        index_task = getattr(request.app.state, "index_task", None)
        if index_task is not None and not index_task.done():
            await index_task
            movies = list(cache.get_all().values())
        if not movies:
            movies = await load_library(settings, cache)

    results = search_service.search(movies, keywords=[], sort=sort)
    return SearchResponse(results=results)

