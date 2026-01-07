"""Tests for domain models.

These tests verify:
1. Model validation works (required fields, type checking)
2. Default values are applied correctly
3. Immutability (frozen models)
4. JSON serialization works
5. Field constraints (e.g., duration_minutes >= 0)
"""

from pathlib import Path

import pytest

from app.domain.movie import (
    MovieFile,
    MovieMetadata,
    SearchRequest,
    SearchResponse,
)


def test_movie_file_creation() -> None:
    """Test that MovieFile can be created with valid data."""
    movie_file = MovieFile(
        file_path=Path("/movies/test.mp4"),
        filename="test.mp4",
        duration_minutes=120,
    )
    
    assert movie_file.file_path == Path("/movies/test.mp4")
    assert movie_file.filename == "test.mp4"
    assert movie_file.duration_minutes == 120


def test_movie_file_validation_negative_duration() -> None:
    """Test that negative duration is rejected."""
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        MovieFile(
            file_path=Path("/movies/test.mp4"),
            filename="test.mp4",
            duration_minutes=-10,  # Invalid: negative duration
        )


def test_movie_file_immutability() -> None:
    """Test that MovieFile instances are immutable (frozen=True).
    
    In Pydantic v2, frozen=True prevents attribute assignment after creation.
    Attempting to modify an attribute raises ValidationError with type 'frozen_instance'.
    """
    from pydantic import ValidationError
    
    movie_file = MovieFile(
        file_path=Path("/movies/test.mp4"),
        filename="test.mp4",
        duration_minutes=120,
    )
    
    # Verify we can access the values
    assert movie_file.duration_minutes == 120
    
    # In Pydantic v2 with frozen=True, attempting to set an attribute raises ValidationError
    with pytest.raises(ValidationError, match="frozen_instance"):
        movie_file.duration_minutes = 150  # This should fail for frozen models


def test_movie_metadata_minimal() -> None:
    """Test MovieMetadata can be created with minimal required fields."""
    metadata = MovieMetadata(
        file_path=Path("/movies/test.mp4"),
        duration_minutes=120,
    )
    
    assert metadata.file_path == Path("/movies/test.mp4")
    assert metadata.duration_minutes == 120
    assert metadata.title is None
    assert metadata.genres == []  # Default empty list
    assert metadata.plot is None


def test_movie_metadata_full() -> None:
    """Test MovieMetadata with all fields populated."""
    metadata = MovieMetadata(
        file_path=Path("/movies/test.mp4"),
        title="Test Movie",
        genres=["Action", "Thriller"],
        plot="An exciting test movie",
        duration_minutes=120,
    )
    
    assert metadata.title == "Test Movie"
    assert metadata.genres == ["Action", "Thriller"]
    assert metadata.plot == "An exciting test movie"


def test_movie_metadata_default_factory_for_genres() -> None:
    """Test that genres defaults to empty list, not None.
    
    Using default_factory=list ensures each instance gets its own list,
    avoiding shared state bugs. If we used default=[], all instances
    would share the same list object.
    """
    metadata1 = MovieMetadata(
        file_path=Path("/movies/test1.mp4"),
        duration_minutes=100,
    )
    metadata2 = MovieMetadata(
        file_path=Path("/movies/test2.mp4"),
        duration_minutes=110,
    )
    
    # Each should have its own empty list (different objects)
    assert metadata1.genres == []
    assert metadata2.genres == []
    assert metadata1.genres is not metadata2.genres  # Different objects


def test_search_request_defaults() -> None:
    """Test SearchRequest has correct default values."""
    request = SearchRequest()
    
    assert request.keywords == []
    assert request.sort == "duration"


def test_search_request_with_values() -> None:
    """Test SearchRequest can be created with custom values."""
    request = SearchRequest(
        keywords=["thriller", "dark"],
        sort="-duration",
    )
    
    assert request.keywords == ["thriller", "dark"]
    assert request.sort == "-duration"


def test_search_response() -> None:
    """Test SearchResponse can be created with results."""
    movies = [
        MovieMetadata(
            file_path=Path("/movies/test1.mp4"),
            title="Movie 1",
            duration_minutes=100,
        ),
        MovieMetadata(
            file_path=Path("/movies/test2.mp4"),
            title="Movie 2",
            duration_minutes=120,
        ),
    ]
    
    response = SearchResponse(results=movies)
    
    assert len(response.results) == 2
    assert response.results[0].title == "Movie 1"
    assert response.results[1].title == "Movie 2"


def test_model_json_serialization() -> None:
    """Test that models can be serialized to JSON.
    
    Pydantic models have built-in JSON serialization via .model_dump_json().
    This is essential for FastAPI, which automatically converts models to JSON.
    """
    movie = MovieMetadata(
        file_path=Path("/movies/test.mp4"),
        title="Test Movie",
        genres=["Action"],
        duration_minutes=120,
    )
    
    # model_dump_json() converts to JSON string
    json_str = movie.model_dump_json()
    
    # Verify it's valid JSON and contains expected fields
    assert '"title":"Test Movie"' in json_str
    assert '"duration_minutes":120' in json_str
    assert '"genres":["Action"]' in json_str


def test_model_json_deserialization() -> None:
    """Test that models can be created from JSON dict.
    
    Pydantic models can be created from dictionaries (e.g., from JSON).
    FastAPI automatically converts incoming JSON to model instances.
    """
    data = {
        "file_path": "/movies/test.mp4",
        "title": "Test Movie",
        "genres": ["Action", "Thriller"],
        "duration_minutes": 120,
    }
    
    movie = MovieMetadata(**data)  # ** unpacks dict as keyword arguments
    
    assert movie.title == "Test Movie"
    assert movie.genres == ["Action", "Thriller"]
    assert movie.duration_minutes == 120
