"""Focused tests for stream extraction, transcoding, and remuxing."""

# Pytest fixtures are intentionally supplied as test-function parameters.
# pylint: disable=redefined-outer-name

from pathlib import Path
from typing import Any, Literal

import pytest

import deocder_main
import demuxer_main
from deocder_main import Transcoder
from demuxer_main import Muxer


class FakeCommand:
    """Minimal ffmpeg-python command chain for unit tests."""

    def __init__(self) -> None:
        self.ran = False
        self.arguments: tuple[str, ...] = ()

    def global_args(self, *_args: str) -> "FakeCommand":
        """Record global FFmpeg arguments and return this fake command."""
        self.arguments = _args
        return self

    def overwrite_output(self) -> "FakeCommand":
        """Return this command to mimic ffmpeg-python's chaining API."""
        return self

    def run(self) -> None:
        """Record execution of the fake command."""
        self.ran = True


class FakeSource:
    """Fake FFmpeg input with audio and video selectors."""

    def __getitem__(self, key: str) -> tuple[str, str]:
        """Return a selector for the requested stream."""
        return ("stream", key)

    @property
    def video(self) -> tuple[str, str]:
        """Return the fake video stream selector."""
        return ("stream", "video")

    @property
    def audio(self) -> tuple[str, str]:
        """Return the fake audio stream selector."""
        return ("stream", "audio")


@pytest.fixture
def source_file(tmp_path: Path) -> Path:
    """Create a minimal temporary source file."""
    path = tmp_path / "input.mp4"
    path.write_bytes(b"dummy media")
    return path


def test_transcoder_builds_expected_stream_options(
    monkeypatch: pytest.MonkeyPatch,
    source_file: Path,
    tmp_path: Path,
) -> None:
    """Map the requested stream types and apply mode-specific codecs."""
    captured: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def fake_probe(path: str) -> dict[str, list[dict[str, str]]]:
        assert Path(path) == source_file
        return {
            "streams": [
                {"codec_type": "video"},
                {"codec_type": "audio"},
            ]
        }

    def fake_input(path: str) -> FakeSource:
        assert Path(path) == source_file
        return FakeSource()

    def fake_output(*args: Any, **options: Any) -> FakeCommand:
        captured.append((args, options))
        return FakeCommand()

    monkeypatch.setattr(
        deocder_main.ffmpeg,
        "probe",
        fake_probe,
    )
    monkeypatch.setattr(deocder_main.ffmpeg, "input", fake_input)
    monkeypatch.setattr(deocder_main.ffmpeg, "output", fake_output)

    transcoder = Transcoder(source_file)
    transcoder.transcode("mkv", tmp_path / "video", stream_mode="video")
    transcoder.transcode("mp3", tmp_path / "audio", stream_mode="audio")
    transcoder.transcode("mp4", tmp_path / "both", stream_mode="both")

    assert captured == [
        ((("stream", "video"), str(tmp_path / "video" / "input.mkv")),
         {"vcodec": "libx264", "an": None}),
        ((("stream", "audio"), str(tmp_path / "audio" / "input.mp3")),
         {"vn": None, "acodec": "libmp3lame"}),
        ((("stream", "video"), ("stream", "audio"),
          str(tmp_path / "both" / "input.mp4")),
         {"vcodec": "libx264", "acodec": "aac"}),
    ]


@pytest.mark.parametrize(
    ("mode", "output_format"),
    [("video", "mp3"), ("both", "aac"), ("audio", "mkv")],
)
def test_transcoder_rejects_incompatible_mode_and_container(
    source_file: Path,
    mode: Literal["video", "audio", "both"],
    output_format: str,
) -> None:
    """Reject container formats that cannot hold the selected streams."""
    with pytest.raises(ValueError):
        Transcoder(source_file).transcode(
            output_format,
            source_file.parent / "output",
            stream_mode=mode,
        )


def test_transcoder_rejects_missing_required_stream(
    monkeypatch: pytest.MonkeyPatch,
    source_file: Path,
) -> None:
    """Reject transcoding when the requested stream is absent."""
    def fake_probe(path: str) -> dict[str, list[dict[str, str]]]:
        assert Path(path) == source_file
        return {"streams": [{"codec_type": "audio"}]}

    monkeypatch.setattr(
        deocder_main.ffmpeg,
        "probe",
        fake_probe,
    )
    with pytest.raises(ValueError, match="video"):
        Transcoder(source_file).transcode(
            "mkv",
            source_file.parent / "output",
            stream_mode="video",
        )


def test_extraction_uses_selected_stream_and_safe_output(
    monkeypatch: pytest.MonkeyPatch,
    source_file: Path,
    tmp_path: Path,
) -> None:
    """Extract the requested ordinal stream to a safe destination path."""
    captured: list[tuple[Any, dict[str, Any]]] = []

    def fake_input(path: str) -> FakeSource:
        assert Path(path) == source_file
        return FakeSource()

    def fake_output(stream: Any, path: str, **options: Any) -> FakeCommand:
        captured.append(((stream, path), options))
        return FakeCommand()

    monkeypatch.setattr(demuxer_main.ffmpeg, "input", fake_input)
    monkeypatch.setattr(demuxer_main.ffmpeg, "output", fake_output)

    output = Muxer(source_file).muxing(
        "audio",
        "aac",
        "audio_track",
        tmp_path / "tracks",
        stream_index=1,
    )

    assert output == tmp_path / "tracks" / "audio_track.aac"
    assert captured == [
        ((("stream", "a:1"), str(output)), {"acodec": "copy"})
    ]


def test_remux_copies_all_streams_and_rejects_audio_only_containers(
    monkeypatch: pytest.MonkeyPatch,
    source_file: Path,
    tmp_path: Path,
) -> None:
    """Remux all streams and disallow audio-only output containers."""
    captured: list[dict[str, Any]] = []

    def fake_input(path: str) -> FakeSource:
        assert Path(path) == source_file
        return FakeSource()

    def fake_output(source: Any, path: str, **options: Any) -> FakeCommand:
        assert isinstance(source, FakeSource)
        assert Path(path).suffix == ".mkv"
        captured.append(options)
        return FakeCommand()

    monkeypatch.setattr(demuxer_main.ffmpeg, "input", fake_input)
    monkeypatch.setattr(demuxer_main.ffmpeg, "output", fake_output)

    output = Muxer(source_file).remuxing(output_format="mkv", output_dir=tmp_path)
    assert output == tmp_path / "input.mkv"
    assert captured == [{"codec": "copy", "map": "0"}]

    with pytest.raises(ValueError, match="Supported remux formats"):
        Muxer(source_file).remuxing(output_format="mp3", output_dir=tmp_path)
