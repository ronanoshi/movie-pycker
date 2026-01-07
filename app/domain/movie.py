"""Domain models for movie data structures.

These Pydantic models define the shape of data in our application:
- MovieFile: Raw file information extracted from disk
- MovieMetadata: Complete movie data (file + enriched metadata)
- SearchRequest/Response: API contract models

Pydantic models provide:
1. Automatic validation (type checking, required fields)
2. JSON serialization/deserialization
3. IDE autocomplete and type hints
4. Documentation generation for FastAPI
"""

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field


class MovieFile(BaseModel):
    """Raw movie file information extracted from disk.
    
    This represents a video file before enrichment with OMDb data.
    We use Pydantic BaseModel instead of dataclasses because:
    1. Automatic JSON serialization for API responses
    2. Built-in validation (e.g., Path must be valid)
    3. FastAPI integration (automatically generates OpenAPI schema)
    
    The model_config with frozen=True makes instances immutable after creation.
    This prevents accidental modification and makes the code safer.
    """
    
    model_config = {
        "frozen": True,  # Make instances immutable (like dataclass(frozen=True))
    }
    
    file_path: Path = Field(..., description="Full path to the movie file")
    filename: str = Field(..., description="Name of the movie file")
    duration_minutes: int = Field(
        ..., 
        ge=0,  # Greater than or equal to 0 (validation)
        description="Duration of the movie in minutes"
    )


class MovieMetadata(BaseModel):
    """Complete movie metadata combining file info and OMDb enrichment.
    
    This is what we store in cache and return from the API.
    
    Optional fields allow graceful degradation - if OMDb lookup fails,
    we still have the file_path and duration_minutes from MovieFile.
    
    List[str] for genres is better than a comma-separated string because:
    1. Type-safe (IDE knows it's a list)
    2. Easier to search/filter
    3. Better JSON representation
    """
    
    model_config = {
        "frozen": True,
    }
    
    file_path: Path = Field(..., description="Full path to the movie file")
    title: Optional[str] = Field(
        default=None,
        description="Movie title from OMDb (or None if not enriched)"
    )
    genres: List[str] = Field(
        default_factory=list,  # Empty list by default (not None)
        description="List of genres from OMDb"
    )
    plot: Optional[str] = Field(
        default=None,
        description="Movie plot/synopsis from OMDb"
    )
    duration_minutes: int = Field(
        ...,
        ge=0,
        description="Duration of the movie in minutes"
    )


class SearchRequest(BaseModel):
    """Request model for movie search endpoint.
    
    This defines the API contract for POST /movies/search.
    FastAPI automatically validates incoming JSON against this model.
    
    List[str] allows multiple keywords for flexible searching.
    The sort field uses string to allow future extensions (rating, year, etc.).
    """
    
    keywords: List[str] = Field(
        default_factory=list,
        description="Keywords to search for in title, genres, or plot"
    )
    sort: str = Field(
        default="duration",
        description="Sort field (e.g., 'duration' or '-duration' for descending)"
    )


class SearchResponse(BaseModel):
    """Response model for movie search endpoint.
    
    Wrapping results in a model (instead of returning List directly) allows:
    1. Future extensibility (can add pagination, total count, etc.)
    2. Consistent API response format
    3. Better OpenAPI documentation
    """
    
    results: List[MovieMetadata] = Field(
        ...,
        description="List of movies matching search criteria"
    )


