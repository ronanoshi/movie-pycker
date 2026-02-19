"""Tests for the indexer service."""

from __future__ import annotations

from pathlib import Path
from typing import List

import pytest

from app.domain.movie import MovieFile
from app.infrastructure.media_info import MediaInfoExtractor
from app.services.indexer import Indexer


class _FakeExtractor(MediaInfoExtractor):
    """Simple extractor for tests."""

    def __init__(self, duration_minutes: int = 120) -> None:
        self.duration_minutes = duration_minutes
        self.seen_paths: List[Path] = []

    def extract_duration_minutes(self, file_path: Path) -> int:
        self.seen_paths.append(file_path)
        return self.duration_minutes


def test_scan_directory_filters_supported_extensions(tmp_path: Path) -> None:
    extractor = _FakeExtractor(duration_minutes=90)
    indexer = Indexer(extractor)

    # Supported files
    movie1 = tmp_path / "movie1.mp4"
    movie2 = tmp_path / "movie2.MKV"
    movie3 = tmp_path / "movie3.avi"
    for file_path in (movie1, movie2, movie3):
        file_path.write_text("data")

    # Unsupported files
    (tmp_path / "notes.txt").write_text("ignore")
    (tmp_path / "image.jpg").write_text("ignore")

    results = indexer.scan_directory(tmp_path)

    assert len(results) == 3
    assert {movie.file_path for movie in results} == {movie1, movie2, movie3}


def test_scan_directory_handles_missing_directory(
    caplog: pytest.LogCaptureFixture
) -> None:
    extractor = _FakeExtractor()
    indexer = Indexer(extractor)
    missing = Path("/path/does/not/exist")

    with caplog.at_level("WARNING"):
        results = indexer.scan_directory(missing)

    assert results == []
    assert any("does not exist" in record.message for record in caplog.records)


def test_scan_directory_handles_file_path(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture
) -> None:
    extractor = _FakeExtractor()
    indexer = Indexer(extractor)
    file_path = tmp_path / "not_a_dir.mp4"
    file_path.write_text("data")

    with caplog.at_level("WARNING"):
        results = indexer.scan_directory(file_path)

    assert results == []
    assert any("not a directory" in record.message for record in caplog.records)


def test_scan_directory_returns_movie_files(tmp_path: Path) -> None:
    extractor = _FakeExtractor(duration_minutes=123)
    indexer = Indexer(extractor)

    movie = tmp_path / "movie.mp4"
    movie.write_text("data")

    results = indexer.scan_directory(tmp_path)

    assert results == [
        MovieFile(
            file_path=movie,
            filename="movie.mp4",
            duration_minutes=123,
        )
    ]
    assert extractor.seen_paths == [movie]
