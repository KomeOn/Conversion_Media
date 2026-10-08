"""Unit tests for the project's entrypoint and supporting modules."""

# These tests directly exercise the console's internal selection and exit helpers.
# pylint: disable=protected-access

import json
import runpy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import file_main
import fixed_values
from fixed_values import constants
import media
from media import print_media_report, utility_functions
import path_helper
import utilities
from utilities import ffmpeg_utils, file_ops, platform_name


def test_app_main_invokes_runner(monkeypatch: pytest.MonkeyPatch) -> None:
    """The executable entrypoint exits with the application runner's result."""
    monkeypatch.setattr(file_main, "run", lambda: 7)
    with pytest.raises(SystemExit) as error:
        runpy.run_path(
            str(Path(__file__).parents[1] / "app_main.py"),
            run_name="__main__",
        )
    assert error.value.code == 7


def test_fixed_values_constants() -> None:
    """Advertised formats are built from the specific video and audio groups."""
    assert constants.VIDEO_CONTAINER_FORMATS == ("mp4", "mkv")
    assert constants.AUDIO_CONTAINER_FORMATS == ("aac", "mp3")
    assert constants.SUPPORTED_FORMAT == ["mp4", "mkv", "aac", "mp3"]
    assert constants.REMUX_FORMATS == constants.VIDEO_CONTAINER_FORMATS
    assert "GNU GPL v3.0" in constants.TERMS_CONDITIONS


def test_fixed_values_package_exports_constants_module() -> None:
    """The constants package imports successfully."""
    assert fixed_values is not None


def test_media_package_exports_public_classes() -> None:
    """The media package exposes its documented public API."""
    assert media.MediaInspector.__name__ == "MediaInspector"
    assert media.PrintMedia.__name__ == "PrintMedia"


def test_utilities_package_imports() -> None:
    """The utilities package imports successfully."""
    assert utilities is not None


def test_path_helper_converts_paths_and_reports_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Path conversion invokes wslpath with the appropriate direction."""
    calls: list[list[str]] = []

    def fake_run(command: list[str], **_kwargs: Any) -> SimpleNamespace:
        calls.append(command)
        return SimpleNamespace(stdout="/mnt/c/media.mp4\n")

    monkeypatch.setattr(path_helper.subprocess, "run", fake_run)
    assert path_helper.to_wsl_path(r"C:\media.mp4") == "/mnt/c/media.mp4"
    assert path_helper.to_win_path("/mnt/c/media.mp4") == "/mnt/c/media.mp4"
    assert calls == [
        ["wslpath", "-u", r"C:\media.mp4"],
        ["wslpath", "-w", "/mnt/c/media.mp4"],
    ]

    with pytest.raises(ValueError, match="must not be empty"):
        path_helper.to_wsl_path("")

    def missing_wslpath(*_args: Any, **_kwargs: Any) -> None:
        raise FileNotFoundError

    monkeypatch.setattr(path_helper.subprocess, "run", missing_wslpath)
    with pytest.raises(RuntimeError, match="wslpath was not found"):
        path_helper.to_wsl_path(r"C:\media.mp4")


def test_platform_name_returns_system_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The platform helper delegates to Python's platform module."""
    monkeypatch.setattr(platform_name.platform, "system", lambda: "TestOS")
    assert platform_name.platform_system() == "TestOS"


def test_ffmpeg_utils_decodes_error_output() -> None:
    """FFmpeg stderr bytes and text are returned as readable details."""
    byte_error = ffmpeg_utils.ffmpeg.Error("ffmpeg", b"", b"failure \xff")
    text_error = ffmpeg_utils.ffmpeg.Error("ffmpeg", b"", "text failure")
    empty_error = ffmpeg_utils.ffmpeg.Error("ffmpeg", b"", None)

    assert "failure" in ffmpeg_utils.get_error_details(byte_error)
    assert ffmpeg_utils.get_error_details(text_error) == "text failure"
    assert ffmpeg_utils.get_error_details(empty_error) == ""


def test_file_ops_dispatches_by_platform(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The file-picker entrypoint selects the matching platform backend."""
    monkeypatch.setattr(file_ops, "platform_system", lambda: "Windows")
    monkeypatch.setattr(file_ops, "windows_file_picker", lambda: "C:/media.mp4")
    assert file_ops.open_files() == "C:/media.mp4"

    monkeypatch.setattr(file_ops, "platform_system", lambda: "Darwin")
    monkeypatch.setattr(file_ops, "macos_file_picker", lambda: "/media.mp4")
    assert file_ops.open_files() == "/media.mp4"

    monkeypatch.setattr(file_ops, "platform_system", lambda: "Plan9")
    with pytest.raises(RuntimeError, match="Unsupported operating system"):
        file_ops.open_files()


def test_file_ops_dispatches_linux_and_wsl(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Linux uses its picker, while WSL converts the Windows picker path."""
    monkeypatch.setattr(file_ops, "platform_system", lambda: "Linux")
    monkeypatch.setattr(file_ops, "is_wsl", lambda: False)
    monkeypatch.setattr(file_ops, "linux_file_picker", lambda: "/media.mp4")
    assert file_ops.open_files() == "/media.mp4"

    monkeypatch.setattr(file_ops, "is_wsl", lambda: True)
    monkeypatch.setattr(file_ops, "windows_file_picker", lambda: r"C:\media.mp4")
    monkeypatch.setattr(file_ops, "to_wsl_path", lambda _path: "/mnt/c/media.mp4")
    assert file_ops.open_files() == "/mnt/c/media.mp4"


def test_utility_functions_format_values_and_report() -> None:
    """Media metadata formatters build readable values and report sections."""
    assert utility_functions.format_duration(65) == "00:01:05.000"
    assert utility_functions.format_duration(None) == "-"
    assert utility_functions.format_bitrate(128000) == "128.00 kb/s"
    assert utility_functions.format_size(1024) == "1.00 KB"
    assert utility_functions.format_frame_rate("30/1") == "30.00 fps"
    assert utility_functions.format_frame_rate("N/A") == "-"
    assert utility_functions.format_frame_rate("unknown") == "unknown"

    text = utility_functions.report(
        {
            "Summary": {"format": "mp4", "duration": "5", "size": "2048"},
            "Video": [{"index": 0, "codec_type": "video", "codec_name": "h264"}],
            "Audio": [],
            "Subtitle": [],
            "Metadata": {"title": "Demo"},
        },
        "demo.mp4",
    )
    assert "Name        : demo.mp4" in text
    assert "Video Streams" in text
    assert "Codec       : h264" in text
    assert "title               : Demo" in text


def test_print_media_report_saves_and_prints(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Report helpers persist valid JSON and print both report formats."""
    printer = print_media_report.PrintMedia()
    data = {"Summary": {"format": "mp4"}, "Video": [], "Audio": []}

    path = printer.save_json_report(data, tmp_path, "module-report.json")
    assert json.loads(path.read_text(encoding="utf-8")) == data

    printed_json = printer.print_json_report(data)
    assert json.loads(printed_json) == data
    assert printed_json in capsys.readouterr().out

    readable = printer.print_readable_report(data, "demo.mp4")
    assert "Name        : demo.mp4" in readable


def test_file_main_renders_console_and_media_headers() -> None:
    """The console helpers include the app, operation choices, and summary."""
    assert constants.APP_NAME in file_main.console_header()
    menu = file_main.app_menu()
    assert "Extract audio or video" in menu
    assert "Remux all streams" in menu
    assert "Exit" in menu

    header = file_main.media_header(
        {
            "filename": "/media/demo.mp4",
            "format": "mp4",
            "duration": "5",
            "size": "1024",
            "video_streams": 1,
            "audio_streams": 1,
            "subtitle_streams": 0,
        }
    )
    assert "demo.mp4" in header
    assert "1 video, 1 audio, 0 subtitle" in header


def test_file_main_selects_extraction_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Stream selection handles valid indices and invalid user input."""
    streams = {"video": [{"codec_name": "h264", "tags": {"title": "Main"}}]}
    answers = iter(("video", "0"))
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    assert file_main._select_extraction_stream(streams) == ("video", 0)

    answers = iter(("video", "invalid"))
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    assert file_main._select_extraction_stream(streams) is None

    assert file_main._select_extraction_stream({"video": [], "audio": []}) is None


def test_file_main_conversion_and_remux_workflows(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The conversion and remux prompts call their respective APIs."""
    calls: list[tuple[str, dict[str, Any]]] = []

    # These minimal fakes intentionally implement only the called public method.
    # pylint: disable=too-few-public-methods
    class FakeTranscoder:
        """Capture calls made by the console transcoding workflow."""

        def __init__(self, _path: Path) -> None:
            """Accept the selected media path."""
            self.path = _path

        def transcode(self, output_format: str, **options: Any) -> Path:
            """Record the requested transcode and return its output path."""
            calls.append((output_format, options))
            return Path(f"converted/output.{output_format}")

    class FakeMuxer:
        """Capture calls made by the console remux workflow."""

        def __init__(self, _path: Path) -> None:
            """Accept the selected media path."""
            self.path = _path

        def remuxing(self, **options: Any) -> Path:
            """Record the remux options and return a representative path."""
            calls.append(("remux", options))
            return Path("remuxed/output.mkv")

    monkeypatch.setattr(file_main, "Transcoder", FakeTranscoder)
    monkeypatch.setattr(file_main, "Muxer", FakeMuxer)
    media_stub = SimpleNamespace(file_path=Path("input.mp4"))

    answers = iter(("1", "mkv", "mkv"))
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    file_main.convert_media(media_stub)
    file_main.remux_media(media_stub)

    assert calls == [
        ("mkv", {"stream_mode": "video"}),
        ("remux", {"output_format": "mkv"}),
    ]
    output = capsys.readouterr().out
    assert "Transcoding complete" in output
    assert "Remux complete" in output


def test_file_main_exit_and_interrupt_handling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exit can save a report, and run converts an interrupt to a clean code."""
    saved: list[bool] = []
    media_stub = SimpleNamespace(save_report=lambda: saved.append(True))
    answers = iter(("yes", "yes"))
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    assert file_main._confirm_exit(media_stub) is True
    assert saved == [True]

    monkeypatch.setattr(
        file_main,
        "main",
        lambda: (_ for _ in ()).throw(KeyboardInterrupt),
    )
    assert file_main.run() == 0


def test_file_main_main_handles_cancelled_picker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cancelling the file picker exits without entering the menu."""
    monkeypatch.setattr(file_main, "open_files", lambda: None)
    assert file_main.main() == 0
