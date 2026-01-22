"""Tests for media metadata extraction using pymediainfo."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.media_info import PyMediaInfoExtractor


def _mock_track(track_type: str | None, duration: float | None) -> MagicMock:
    track = MagicMock()
    track.track_type = track_type
    track.duration = duration
    return track


def test_extract_duration_success() -> None:
    """Extracts duration from a valid General track."""
    extractor = PyMediaInfoExtractor()
    file_path = Path("/movies/test.mp4")

    media_info = MagicMock()
    media_info.tracks = [_mock_track("General", 7 * 60 * 1000)]

    with patch("app.infrastructure.media_info.MediaInfo.parse", return_value=media_info):
        assert extractor.extract_duration_minutes(file_path) == 7


def test_extract_duration_no_duration_logs_warning(caplog: pytest.LogCaptureFixture) -> None:
    """Returns 0 when duration is missing and logs a warning."""
    extractor = PyMediaInfoExtractor()
    file_path = Path("/movies/test.mp4")

    media_info = MagicMock()
    media_info.tracks = [_mock_track("General", None)]

    with patch("app.infrastructure.media_info.MediaInfo.parse", return_value=media_info):
        with caplog.at_level("WARNING"):
            assert extractor.extract_duration_minutes(file_path) == 0

    assert any("No duration found" in record.message for record in caplog.records)


def test_extract_duration_exception_logs_warning(caplog: pytest.LogCaptureFixture) -> None:
    """Returns 0 when pymediainfo raises and logs a warning."""
    extractor = PyMediaInfoExtractor()
    file_path = Path("/movies/test.mp4")

    with patch("app.infrastructure.media_info.MediaInfo.parse", side_effect=RuntimeError("boom")):
        with caplog.at_level("WARNING"):
            assert extractor.extract_duration_minutes(file_path) == 0

    assert any("Failed to extract duration" in record.message for record in caplog.records)

