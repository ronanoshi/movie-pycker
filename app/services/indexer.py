"""Movie library indexer service."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List

from app.domain.movie import MovieFile
from app.infrastructure.media_info import MediaInfoExtractor

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".mp4", ".mkv", ".avi"}


class Indexer:
    """Scans a directory and extracts basic file metadata."""

    def __init__(self, extractor: MediaInfoExtractor) -> None:
        self._extractor = extractor

    def scan_directory(self, directory: Path) -> List[MovieFile]:
        """Scan directory for supported video files."""
        if not directory.exists():
            logger.warning("Movie directory does not exist: %s", directory)
            return []

        if not directory.is_dir():
            logger.warning("Movie path is not a directory: %s", directory)
            return []

        results: List[MovieFile] = []
        for file_path in _iter_video_files(directory):
            try:
                duration_minutes = self._extractor.extract_duration_minutes(file_path)
            except Exception as exc:  # noqa: BLE001 - defensive, extractor may raise
                logger.warning("Failed to extract duration for %s: %s", file_path, exc)
                duration_minutes = 0

            results.append(
                MovieFile(
                    file_path=file_path,
                    filename=file_path.name,
                    duration_minutes=duration_minutes,
                )
            )

        return results


def _iter_video_files(directory: Path) -> Iterable[Path]:
    """Yield supported video files under the directory."""
    for path in directory.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path

