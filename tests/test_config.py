"""Tests for configuration management.

These tests verify that:
1. Settings load correctly from environment variables
2. Validation works (invalid paths, empty API keys, etc.)
3. Default values are applied correctly
4. .env file loading works

We use pytest fixtures to set up test environments with temporary configs.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.config import Settings


@pytest.fixture
def temp_movie_directory() -> Path:
    """Create a temporary directory for testing.

    pytest fixtures are a way to provide test dependencies.
    Any test function that takes 'temp_movie_directory' as a parameter
    will automatically receive this Path object.

    Using tempfile.mkdtemp() ensures we clean up after tests.
    """
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)  # 'yield' returns the value but continues execution after test
    # Cleanup happens here after test completes


@pytest.fixture
def env_vars(temp_movie_directory: Path) -> dict:
    """Provide environment variables for testing.

    This fixture returns a dict of env vars that can be patched into os.environ.
    Python's unittest.mock.patch allows us to temporarily modify os.environ
    without affecting the actual environment.
    """
    return {
        "MOVIE_DIRECTORY": str(temp_movie_directory),
        "OMDB_API_KEY": "test_api_key_123",
    }


def test_settings_load_from_env_vars(
    env_vars: dict,
    temp_movie_directory: Path
) -> None:
    """Test that settings load correctly from environment variables."""
    # patch.dict temporarily replaces os.environ with our test values
    # The 'with' statement ensures cleanup after the block
    with patch.dict(os.environ, env_vars, clear=True):
        settings = Settings(_env_file=None)

        assert settings.movie_directory == temp_movie_directory
        assert settings.omdb_api_key == "test_api_key_123"
        assert settings.auto_index_on_startup is True  # Default value
        assert settings.enable_cache is True  # Default value


def test_settings_default_values(env_vars: dict) -> None:
    """Test that default values are applied correctly."""
    with patch.dict(os.environ, env_vars, clear=True):
        settings = Settings(_env_file=None)

        assert settings.cache_file is None  # Default None
        assert settings.auto_index_on_startup is True  # Default True
        assert settings.enable_cache is True  # Default True


def test_settings_case_insensitive(env_vars: dict, temp_movie_directory: Path) -> None:
    """Test that environment variable names are case-insensitive."""
    # Use lowercase keys to test case insensitivity
    lower_case_vars = {
        "movie_directory": str(temp_movie_directory),
        "omdb_api_key": "test_key",
    }

    with patch.dict(os.environ, lower_case_vars, clear=True):
        settings = Settings(_env_file=None)
        assert settings.movie_directory == temp_movie_directory
        assert settings.omdb_api_key == "test_key"


def test_settings_validate_movie_directory_nonexistent(env_vars: dict) -> None:
    """Test validation fails when movie directory doesn't exist."""
    env_vars["MOVIE_DIRECTORY"] = "/nonexistent/path/that/does/not/exist"

    with patch.dict(os.environ, env_vars, clear=True):
        # pytest.raises verifies that a ValueError is raised
        with pytest.raises(ValueError, match="does not exist"):
            Settings(_env_file=None)


def test_settings_validate_movie_directory_not_a_directory(
    env_vars: dict,
    temp_movie_directory: Path,
) -> None:
    """Test validation fails when movie directory is actually a file."""
    # Create a file instead of using the directory
    test_file = temp_movie_directory / "test.txt"
    test_file.touch()

    env_vars["MOVIE_DIRECTORY"] = str(test_file)

    with patch.dict(os.environ, env_vars, clear=True):
        with pytest.raises(ValueError, match="not a directory"):
            Settings(_env_file=None)


def test_settings_validate_empty_omdb_api_key(env_vars: dict) -> None:
    """Test validation fails when OMDb API key is empty."""
    env_vars["OMDB_API_KEY"] = ""

    with patch.dict(os.environ, env_vars, clear=True):
        with pytest.raises(ValueError, match="cannot be empty"):
            Settings(_env_file=None)


def test_settings_validate_whitespace_omdb_api_key(env_vars: dict) -> None:
    """Test that whitespace-only API keys are stripped and validated."""
    env_vars["OMDB_API_KEY"] = "   "  # Only whitespace

    with patch.dict(os.environ, env_vars, clear=True):
        with pytest.raises(ValueError, match="cannot be empty"):
            Settings(_env_file=None)


def test_settings_auto_index_can_be_false(env_vars: dict) -> None:
    """Test that auto_index_on_startup can be set to False."""
    env_vars["AUTO_INDEX_ON_STARTUP"] = "false"

    with patch.dict(os.environ, env_vars, clear=True):
        settings = Settings(_env_file=None)
        assert settings.auto_index_on_startup is False


def test_settings_enable_cache_can_be_false(env_vars: dict) -> None:
    """Test that enable_cache can be set to False."""
    env_vars["ENABLE_CACHE"] = "false"

    with patch.dict(os.environ, env_vars, clear=True):
        settings = Settings(_env_file=None)
        assert settings.enable_cache is False


def test_settings_cache_file_path(env_vars: dict) -> None:
    """Test that cache_file can be set to a specific path."""
    cache_path = Path("/tmp/cache.json")
    env_vars["CACHE_FILE"] = str(cache_path)

    with patch.dict(os.environ, env_vars, clear=True):
        settings = Settings(_env_file=None)
        assert settings.cache_file == cache_path


def test_settings_noise_tokens_default_is_empty(env_vars: dict) -> None:
    """Test that get_noise_tokens() returns an empty list when not set."""
    with patch.dict(os.environ, env_vars, clear=True):
        settings = Settings(_env_file=None)
        assert settings.get_noise_tokens() == []


def test_settings_noise_tokens_from_comma_separated_string(env_vars: dict) -> None:
    """Test that a comma-separated env var is parsed into a list."""
    env_vars["FILENAME_NOISE_TOKENS"] = "1080p,BluRay,x265"

    with patch.dict(os.environ, env_vars, clear=True):
        settings = Settings(_env_file=None)
        assert settings.get_noise_tokens() == ["1080p", "BluRay", "x265"]


def test_settings_noise_tokens_strips_whitespace(env_vars: dict) -> None:
    """Test that whitespace around tokens is trimmed."""
    env_vars["FILENAME_NOISE_TOKENS"] = " 1080p , BluRay , x265 "

    with patch.dict(os.environ, env_vars, clear=True):
        settings = Settings(_env_file=None)
        assert settings.get_noise_tokens() == ["1080p", "BluRay", "x265"]


def test_settings_noise_tokens_ignores_empty_entries(env_vars: dict) -> None:
    """Test that empty entries from extra commas are discarded."""
    env_vars["FILENAME_NOISE_TOKENS"] = "1080p,,BluRay,"

    with patch.dict(os.environ, env_vars, clear=True):
        settings = Settings(_env_file=None)
        assert settings.get_noise_tokens() == ["1080p", "BluRay"]


def test_settings_noise_tokens_supports_compound_tokens(env_vars: dict) -> None:
    """Test that compound tokens (with hyphens or spaces) survive parsing."""
    env_vars["FILENAME_NOISE_TOKENS"] = "WEBRip-WORLD,Ac3 SNAKE,1080p"

    with patch.dict(os.environ, env_vars, clear=True):
        settings = Settings(_env_file=None)
        assert settings.get_noise_tokens() == [
            "WEBRip-WORLD",
            "Ac3 SNAKE",
            "1080p",
        ]
