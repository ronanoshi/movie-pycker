"""FastAPI application entrypoint."""

import asyncio
from contextlib import asynccontextmanager
from contextlib import suppress

from fastapi import FastAPI

from app.api.movies import router as movies_router
from app.core.config import get_settings
from app.infrastructure.cache import InMemoryCache
from app.infrastructure.media_info import PyMediaInfoExtractor
from app.infrastructure.omdb_client import OMDbClient
from app.services.indexer import Indexer
from app.services.metadata_enrichment import MetadataEnrichmentService


async def _index_movies(settings, cache: InMemoryCache) -> None:
    extractor = PyMediaInfoExtractor()
    indexer = Indexer(extractor)
    movie_files = indexer.scan_directory(settings.movie_directory)

    omdb_client = OMDbClient(api_key=settings.omdb_api_key)
    enrichment = MetadataEnrichmentService(omdb_client, cache)
    await enrichment.enrich_movies(movie_files)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load settings and index/enrich movies on startup if enabled."""
    settings = get_settings()
    cache = InMemoryCache()
    app.state.cache = cache
    app.state.settings = settings

    index_task = None
    if settings.auto_index_on_startup:
        index_task = asyncio.create_task(_index_movies(settings, cache))
        app.state.index_task = index_task

    try:
        yield
    finally:
        if index_task and not index_task.done():
            index_task.cancel()
            with suppress(asyncio.CancelledError):
                await index_task


app = FastAPI(title="Movie Pycker", lifespan=lifespan)
app.include_router(movies_router)

