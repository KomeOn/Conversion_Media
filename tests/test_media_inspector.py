"""Tests for inspecting and reporting FFprobe media data."""

# Pytest fixtures are intentionally supplied as test-function parameters.
# pylint: disable=redefined-outer-name

import json
from pathlib import Path
from typing import Any

import pytest

import media.media_inspector as inspector_module
from media.media_inspector import MediaInspector


@pytest.fixture
def media_file(tmp_path: Path) -> Path:
    """Create a dummy file accepted by the inspector constructor."""
    path = tmp_path / "sample.mp4"
    path.write_bytes(b"test")
    return path


@pytest.fixture
def probe_data() -> dict[str, Any]:
    """Return representative FFprobe output."""
    return {
        "format": {
            "filename": "/tmp/sample.mp4",
            "format_name": "mov,mp4",
            "format_long_name": "QuickTime / MOV",
            "duration": "12.5",
            "size": "1024",
            "bit_rate": "128000",
            "nb_streams": 3,
            "tags": {"title": "Sample"},
        },
        "streams": [
            {
                "index": 0,
                "codec_type": "video",
                "codec_name": "h264",
                "profile": "High",
                "width": 1920,
                "height": 1080,
                "avg_frame_rate": "30/1",
                "pix_fmt": "yuv420p",
                "bit_rate": "100000",
                "tags": {"language": "eng", "title": "Picture"},
            },
            {
                "index": 1,
                "codec_type": "audio",
                "codec_name": "aac",
                "channels": 2,
                "channel_layout": "stereo",
                "sample_rate": "48000",
                "bit_rate": "128000",
                "tags": {"language": "eng"},
            },
            {
                "index": 2,
                "codec_type": "subtitle",
                "codec_name": "mov_text",
                "tags": {"language": "eng", "title": "Captions"},
            },
        ],
        "chapters": [{"id": 0, "start_time": "0", "tags": {"title": "Start"}}],
    }


def test_constructor_validates_input_paths(tmp_path: Path, media_file: Path) -> None:
    """Reject missing and non-file inputs while accepting an existing file."""
    assert MediaInspector(media_file).file_path == media_file

    with pytest.raises(FileNotFoundError):
        MediaInspector(tmp_path / "missing.mp4")

    with pytest.raises(ValueError, match="not a file"):
        MediaInspector(tmp_path)


def test_get_media_details_caches_probe(
    monkeypatch: pytest.MonkeyPatch,
    media_file: Path,
    probe_data: dict[str, Any],
) -> None:
    """Probe media once and reuse the cached result."""
    calls: list[dict[str, Any]] = []

    def fake_probe(**kwargs: Any) -> dict[str, Any]:
        """Return fixture data and record the probe invocation."""
        calls.append(kwargs)
        return probe_data

    monkeypatch.setattr(
        inspector_module.ffmpeg,
        "probe",
        fake_probe,
    )

    inspector = MediaInspector(media_file)
    assert inspector.get_media_details() == probe_data
    assert inspector.get_media_details() == probe_data
    assert calls == [{"filename": str(media_file)}]


def test_probe_errors_include_ffprobe_stderr(
    monkeypatch: pytest.MonkeyPatch,
    media_file: Path,
) -> None:
    """Include FFprobe stderr when probing fails."""
    error = inspector_module.ffmpeg.Error("ffprobe", b"", b"invalid media")

    def raise_probe_error(**kwargs: Any) -> dict[str, Any]:
        """Raise the configured probe failure for the expected input."""
        assert kwargs == {"filename": str(media_file)}
        raise error

    monkeypatch.setattr(
        inspector_module.ffmpeg,
        "probe",
        raise_probe_error,
    )

    with pytest.raises(RuntimeError, match="invalid media"):
        MediaInspector(media_file).get_media_details()


def test_streams_summary_and_format(
    monkeypatch: pytest.MonkeyPatch,
    media_file: Path,
    probe_data: dict[str, Any],
) -> None:
    """Normalize and count all supported media stream types."""
    def fake_probe(**kwargs: Any) -> dict[str, Any]:
        """Return fixture probe data for the expected input."""
        assert kwargs == {"filename": str(media_file)}
        return probe_data

    monkeypatch.setattr(inspector_module.ffmpeg, "probe", fake_probe)
    inspector = MediaInspector(media_file)

    assert len(inspector.extract_video_streams()) == 1
    assert len(inspector.extract_audio_streams()) == 1
    assert len(inspector.extract_subtitle_streams()) == 1
    assert inspector.extract_data_streams() == []
    assert inspector.extract_attachment_streams() == []
    assert inspector.get_metadata() == {"title": "Sample"}
    assert inspector.get_chapters() == probe_data["chapters"]
    assert inspector.get_format() == {
        "Filename": "/tmp/sample.mp4",
        "Format Names": ["mov", "mp4"],
        "Stream Count": 3,
        "Duration": "12.5",
        "Creation Time": 0,
    }
    assert inspector.get_summary() == {
        "filename": "/tmp/sample.mp4",
        "format": "mov,mp4",
        "format_long_name": "QuickTime / MOV",
        "duration": "12.5",
        "size": "1024",
        "bit_rate": "128000",
        "video_streams": 1,
        "audio_streams": 1,
        "subtitle_streams": 1,
    }


def test_report_save_and_text_rendering(
    monkeypatch: pytest.MonkeyPatch,
    media_file: Path,
    probe_data: dict[str, Any],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Persist JSON and render the readable report."""
    def fake_probe(**kwargs: Any) -> dict[str, Any]:
        """Return fixture probe data for the expected input."""
        assert kwargs == {"filename": str(media_file)}
        return probe_data

    monkeypatch.setattr(inspector_module.ffmpeg, "probe", fake_probe)
    inspector = MediaInspector(media_file)

    report = inspector.save_report(tmp_path / "reports")
    report_files = list((tmp_path / "reports").glob("*.json"))
    assert len(report_files) == 1
    assert json.loads(report_files[0].read_text(encoding="utf-8")) == report

    text = inspector.print_text_report()
    output = capsys.readouterr().out
    assert text == output.rstrip("\n")
    assert "Video Streams" in text
    assert "Codec       : h264" in text
    assert "Resolution  : 1920x1080" in text
    assert "Audio Streams" in text
    assert "Sample Rate : 48000 Hz" in text
    assert "Subtitle Streams" in text
    assert "Title       : Captions" in text
