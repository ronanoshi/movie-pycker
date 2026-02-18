"""Tests for startup indexing integration."""

import os
import time
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import app.main as main_module
from app.core.config import Settings
from app.infrastructure.media_info import PyMediaInfoExtractor
from app.infrastructure.omdb_client import OMDbClient
from app.main import app


def test_startup_indexes_movies(tmp_path: Path, monkeypatch) -> None:
    movie_path = tmp_path / "movie.mp4"
    movie_path.write_text("data")

    monkeypatch.setattr(
        PyMediaInfoExtractor,
        "extract_duration_minutes",
        lambda _self, _path: 95,
    )

    async def fake_fetch(_self, _title: str) -> None:
        return None

    monkeypatch.setattr(OMDbClient, "fetch_movie_metadata", fake_fetch)
    monkeypatch.setattr(
        main_module,
        "get_settings",
        lambda: Settings(_env_file=None)
    )

    env_vars = {
        "MOVIE_DIRECTORY": str(tmp_path),
        "OMDB_API_KEY": "test_key",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        with TestClient(app) as client:
            deadline = time.monotonic() + 1.0
            payload = {"results": []}
            response = None
            while time.monotonic() < deadline:
                response = client.get("/movies")
                payload = response.json()
                if len(payload["results"]) == 1:
                    break
                time.sleep(0.01)

    assert response is not None
    assert response.status_code == 200
    assert len(payload["results"]) == 1
    assert payload["results"][0]["duration_minutes"] == 95
    assert payload["results"][0]["title"] is None


def test_startup_skips_indexing_when_disabled(tmp_path: Path, monkeypatch) -> None:
    called = {"extract": 0, "fetch": 0}

    def fake_extract(_self, _path: Path) -> int:
        called["extract"] += 1
        return 0

    async def fake_fetch(_self, _title: str) -> None:
        called["fetch"] += 1
        return None

    monkeypatch.setattr(PyMediaInfoExtractor, "extract_duration_minutes", fake_extract)
    monkeypatch.setattr(OMDbClient, "fetch_movie_metadata", fake_fetch)
    monkeypatch.setattr(
        main_module,
        "get_settings",
        lambda: Settings(_env_file=None)
    )

    env_vars = {
        "MOVIE_DIRECTORY": str(tmp_path),
        "OMDB_API_KEY": "test_key",
        "AUTO_INDEX_ON_STARTUP": "false",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        with TestClient(app) as client:
            response = client.get("/movies")

    assert response.status_code == 200
    payload = response.json()
    assert payload["results"] == []
    assert called == {"extract": 0, "fetch": 0}
