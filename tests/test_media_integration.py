"""End-to-end tests using real FFmpeg and FFprobe processes."""

# Pytest fixtures are intentionally supplied as test-function parameters.
# pylint: disable=redefined-outer-name

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from deocder_main import Transcoder
from demuxer_main import Muxer
from media.media_inspector import MediaInspector


@pytest.fixture
def synthetic_media(tmp_path: Path) -> Path:
    """Generate a short audio/video input using local FFmpeg."""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None or shutil.which("ffprobe") is None:
        pytest.skip("Integration tests require both FFmpeg and FFprobe on PATH")

    source_path = tmp_path / "integration-source.mp4"
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        "testsrc=size=160x120:rate=10",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=1000:sample_rate=44100",
        "-t",
        "1",
        "-c:v",
        "mpeg4",
        "-q:v",
        "5",
        "-c:a",
        "aac",
        "-shortest",
        str(source_path),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)
    return source_path


def test_probe_report_and_remux_preserve_audio_video_data_flow(
    synthetic_media: Path,
    tmp_path: Path,
) -> None:
    """Probe, persist, remux, and re-probe a generated audio/video clip."""
    original = MediaInspector(synthetic_media)
    original_summary = original.get_summary()

    assert original_summary["video_streams"] == 1
    assert original_summary["audio_streams"] == 1
    assert original_summary["duration"] is not None

    report_dir = tmp_path / "reports"
    report_data = original.save_report(report_dir)
    report_files = list(report_dir.glob("*.json"))
    assert len(report_files) == 1
    assert json.loads(report_files[0].read_text(encoding="utf-8")) == report_data

    output_path = Muxer(synthetic_media).remuxing(
        output_format="mkv",
        output_dir=tmp_path / "remuxed",
    )
    assert output_path.is_file()
    assert output_path.stat().st_size > 0

    remuxed = MediaInspector(output_path)
    remuxed_summary = remuxed.get_summary()
    assert remuxed_summary["video_streams"] == original_summary["video_streams"]
    assert remuxed_summary["audio_streams"] == original_summary["audio_streams"]
    assert len(remuxed.extract_video_streams()) == 1
    assert len(remuxed.extract_audio_streams()) == 1


def test_transcoder_output_can_be_probed(
    synthetic_media: Path,
    tmp_path: Path,
) -> None:
    """Transcode an actual generated clip and verify its resulting streams."""
    transcoded_path = Transcoder(synthetic_media).transcode(
        "mkv",
        tmp_path / "converted",
        stream_mode="both",
    )

    assert transcoded_path.is_file()
    assert transcoded_path.stat().st_size > 0
    summary = MediaInspector(transcoded_path).get_summary()
    assert summary["video_streams"] == 1
    assert summary["audio_streams"] == 1
