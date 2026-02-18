"""Cache interface and in-memory implementation.

This module defines a small cache abstraction so we can swap the implementation
later (e.g., Redis) without changing service code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Mapping

from app.domain.movie import MovieMetadata


class Cache(ABC):
    """Abstract cache interface for movie metadata."""

    @abstractmethod
    def get(self, key: str) -> MovieMetadata | None:
        """Return a cached item by key, or None if it doesn't exist."""

    @abstractmethod
    def set(self, key: str, value: MovieMetadata) -> None:
        """Store a value in the cache."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Return True if the key exists in the cache."""

    @abstractmethod
    def clear(self) -> None:
        """Clear all items from the cache."""

    @abstractmethod
    def get_all(self) -> Dict[str, MovieMetadata]:
        """Return all cached items as a dict copy."""


class InMemoryCache(Cache):
    """Simple in-memory cache implementation.

    This is suitable for v1 and is easy to replace with Redis later.
    """

    def __init__(self, initial: Mapping[str, MovieMetadata] | None = None) -> None:
        # Copy initial data to avoid sharing external references.
        self._store: Dict[str, MovieMetadata] = dict(initial) if initial else {}

    def get(self, key: str) -> MovieMetadata | None:
        return self._store.get(key)

    def set(self, key: str, value: MovieMetadata) -> None:
        self._store[key] = value

    def exists(self, key: str) -> bool:
        return key in self._store

    def clear(self) -> None:
        self._store.clear()

    def get_all(self) -> Dict[str, MovieMetadata]:
        # Return a shallow copy to prevent external mutation of internal state.
        return dict(self._store)
