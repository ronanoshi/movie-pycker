"""Load and enrich the movie library from disk."""

from app.core.config import Settings
from app.domain.movie import MovieMetadata
from app.infrastructure.cache import Cache
from app.infrastructure.media_info import PyMediaInfoExtractor
from app.infrastructure.omdb_client import OMDbClient
from app.services.indexer import Indexer
from app.services.metadata_enrichment import MetadataEnrichmentService


async def load_library(settings: Settings, cache: Cache) -> list[MovieMetadata]:
    """Scan the directory and enrich movie metadata using OMDb."""
    extractor = PyMediaInfoExtractor()
    indexer = Indexer(extractor)
    movie_files = indexer.scan_directory(settings.movie_directory)

    omdb_client = OMDbClient(api_key=settings.omdb_api_key)
    enrichment = MetadataEnrichmentService(omdb_client, cache)
    return await enrichment.enrich_movies(movie_files)

