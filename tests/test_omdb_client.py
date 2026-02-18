"""Tests for OMDb API client."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import httpx
import pytest

from app.infrastructure.omdb_client import OMDbClient


class _MockAsyncClient:
    """Minimal async client for mocking httpx.AsyncClient."""

    def __init__(self, response: httpx.Response | Exception) -> None:
        self._response = response

    async def __aenter__(self) -> "_MockAsyncClient":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        return None

    async def get(self, *_args: Any, **_kwargs: Any) -> httpx.Response:
        if isinstance(self._response, Exception):
            raise self._response
        return self._response


def _response_ok(payload: dict[str, Any]) -> httpx.Response:
    """Create an httpx.Response with a request attached for raise_for_status()."""
    request = httpx.Request("GET", "https://www.omdbapi.com/")
    return httpx.Response(200, json=payload, request=request)


@pytest.mark.asyncio
async def test_fetch_movie_metadata_success() -> None:
    client = OMDbClient(api_key="test_key")
    payload = {
        "Response": "True",
        "Title": "Se7en",
        "Genre": "Crime, Thriller",
        "Plot": "Detective story",
        "Runtime": "127 min",
    }
    response = _response_ok(payload)

    with patch(
        "app.infrastructure.omdb_client.httpx.AsyncClient",
        return_value=_MockAsyncClient(response)
    ):
        result = await client.fetch_movie_metadata("Se7en")

    assert result == {
        "title": "Se7en",
        "genres": ["Crime", "Thriller"],
        "plot": "Detective story",
        "runtime_minutes": 127,
    }


@pytest.mark.asyncio
async def test_fetch_movie_metadata_not_found() -> None:
    client = OMDbClient(api_key="test_key")
    payload = {"Response": "False", "Error": "Movie not found!"}
    response = _response_ok(payload)

    with patch(
        "app.infrastructure.omdb_client.httpx.AsyncClient",
        return_value=_MockAsyncClient(response)
    ):
        result = await client.fetch_movie_metadata("Missing")

    assert result is None


@pytest.mark.asyncio
async def test_fetch_movie_metadata_runtime_na() -> None:
    client = OMDbClient(api_key="test_key")
    payload = {
        "Response": "True",
        "Title": "Short",
        "Genre": "Drama",
        "Plot": "Test",
        "Runtime": "N/A",
    }
    response = _response_ok(payload)

    with patch(
        "app.infrastructure.omdb_client.httpx.AsyncClient",
        return_value=_MockAsyncClient(response)
    ):
        result = await client.fetch_movie_metadata("Short")

    assert result == {
        "title": "Short",
        "genres": ["Drama"],
        "plot": "Test",
        "runtime_minutes": None,
    }


@pytest.mark.asyncio
async def test_fetch_movie_metadata_request_error(
    caplog: pytest.LogCaptureFixture
) -> None:
    client = OMDbClient(api_key="test_key")
    request = httpx.Request("GET", "https://www.omdbapi.com/")
    error = httpx.RequestError("boom", request=request)

    with patch(
        "app.infrastructure.omdb_client.httpx.AsyncClient",
        return_value=_MockAsyncClient(error)
    ):
        with caplog.at_level("WARNING"):
            result = await client.fetch_movie_metadata("Error")

    assert result is None
    assert any("OMDb request failed" in record.message for record in caplog.records)
