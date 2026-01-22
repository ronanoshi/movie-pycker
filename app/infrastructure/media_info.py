"""Media metadata extraction using pymediainfo.

This module defines a small abstraction so we can swap implementations later
(e.g., ffprobe) without changing the rest of the codebase.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable

from pymediainfo import MediaInfo

logger = logging.getLogger(__name__)


class MediaInfoExtractor(ABC):
    """Abstract interface for extracting media metadata."""

    @abstractmethod
    def extract_duration_minutes(self, file_path: Path) -> int:
        """Return duration in minutes, or 0 if unavailable."""


class PyMediaInfoExtractor(MediaInfoExtractor):
    """pymediainfo-based metadata extractor."""

    def extract_duration_minutes(self, file_path: Path) -> int:
        try:
            media_info = MediaInfo.parse(str(file_path))
            duration_ms = _extract_duration_ms(media_info.tracks)
        except Exception as exc:  # noqa: BLE001 - broad for resilience
            logger.warning("Failed to extract duration for %s: %s", file_path, exc)
            return 0

        if duration_ms is None:
            logger.warning("No duration found for %s", file_path)
            return 0

        return _normalize_minutes(duration_ms)


def _extract_duration_ms(tracks: Iterable[object]) -> float | None:
    """Extract duration in milliseconds from MediaInfo tracks."""
    for track in tracks:
        track_type = getattr(track, "track_type", None)
        duration = getattr(track, "duration", None)
        if track_type in {"General", "Video"} and duration is not None:
            return float(duration)
    return None


def _normalize_minutes(duration_ms: float) -> int:
    """Normalize milliseconds to integer minutes."""
    if duration_ms <= 0:
        return 0
    return max(0, int(round(duration_ms / 60000)))

