"""Configuration management using Pydantic Settings.

This module uses pydantic-settings to load configuration from environment variables
or .env files. Pydantic automatically validates types and provides helpful error messages.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file.
    
    Pydantic BaseSettings automatically:
    1. Reads from environment variables (case-insensitive)
    2. Reads from .env file if present
    3. Validates types (e.g., ensures movie_directory is a valid Path)
    4. Provides default values where specified
    
    The SettingsConfigDict tells pydantic-settings how to load the config:
    - env_file: Look for .env file
    - case_sensitive: Environment variable names are case-insensitive (standard)
    - extra: Ignore extra fields (prevents errors if .env has unused vars)
    """
    
    # model_config is Pydantic v2 syntax for configuration
    # In v2, we use SettingsConfigDict instead of Config class (v1 syntax)
    model_config = SettingsConfigDict(
        env_file=".env",  # Look for .env file in project root
        env_file_encoding="utf-8",
        case_sensitive=False,  # Environment vars are case-insensitive
        extra="ignore",  # Ignore extra fields in .env file
    )
    
    # Field() allows us to add validation and documentation
    # Path type automatically converts string paths to Path objects
    movie_directory: Path = Field(
        ...,
        description="Path to directory containing movie files",
    )

    omdb_api_key: str = Field(
        ...,
        description="OMDb API key for movie metadata enrichment",
    )

    # Optional fields have default values
    # Path | None is union type syntax (Python 3.10+)
    # Could also write: Optional[Path] = None (older syntax)
    cache_file: Path | None = Field(
        default=None,
        description="Optional path to cache file for persistence",
    )

    auto_index_on_startup: bool = Field(
        default=True,
        description="Automatically index movies when application starts",
    )

    enable_cache: bool = Field(
        default=True,
        description="Enable caching for indexed movies",
    )
    
    @field_validator("movie_directory")
    @classmethod
    def validate_movie_directory(cls, v: Path) -> Path:
        """Validate that movie_directory exists and is a directory.
        
        @field_validator is a Pydantic decorator that runs custom validation
        before the value is assigned. The @classmethod is required because
        validators don't receive 'self' - they're called during object construction.
        
        This is Python's way of ensuring data integrity at the model level.
        """
        # Convert to Path if it's a string (Pydantic does this automatically, but explicit is good)
        path = Path(v)
        
        if not path.exists():
            raise ValueError(f"Movie directory does not exist: {path}")
        
        if not path.is_dir():
            raise ValueError(f"Movie directory is not a directory: {path}")
        
        return path
    
    @field_validator("omdb_api_key")
    @classmethod
    def validate_omdb_api_key(cls, v: str) -> str:
        """Validate that OMDb API key is not empty."""
        if not v or not v.strip():
            raise ValueError("OMDb API key cannot be empty")
        return v.strip()


def get_settings() -> Settings:
    """Factory function to get application settings.
    
    This is a common pattern in Python - a factory function that returns
    a singleton-like Settings instance. Pydantic Settings are cached by default,
    so subsequent calls return the same instance.
    
    Using a function instead of a module-level variable allows for:
    1. Lazy initialization (only loads when needed)
    2. Easy testing (can override in tests)
    3. Clear dependency injection
    """
    return Settings()
