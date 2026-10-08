"""Console interface for inspecting, extracting, and converting media files."""

import shutil
from pathlib import Path
from textwrap import wrap
from typing import Any, Literal, cast

from demuxer_main import Muxer
from deocder_main import Transcoder
from fixed_values.constants import (
    APP_NAME,
    AUDIO_CONTAINER_FORMATS,
    DESCRIPTION,
    REMUX_FORMATS,
    SUPPORTED_FORMAT,
    TERMS_CONDITIONS,
    VIDEO_CONTAINER_FORMATS,
)
from media.media_inspector import MediaInspector
from utilities.file_ops import open_files


def _boxed_lines(values: tuple[str, ...]) -> str:
    """Render strings inside a terminal-width-aware text box."""
    width = max(40, min(shutil.get_terminal_size(fallback=(80, 24)).columns, 100))
    inner_width = width - 4
    border = "*" * width
    content_lines = [
        f"* {line:<{inner_width}} *"
        for value in values
        for line in (wrap(value, width=inner_width) or [""])
    ]
    return "\n".join((border, *content_lines, border))


def console_header() -> str:
    """Return the application's welcome banner."""
    return _boxed_lines(
        (
            f"APPLICATION NAME: {APP_NAME}",
            f"DESCRIPTION: {DESCRIPTION}",
            f"FORMATS: {', '.join(SUPPORTED_FORMAT)}",
            f"TERMS AND CONDITIONS: {TERMS_CONDITIONS}",
        )
    )


def app_menu() -> str:
    """Return the main menu."""
    return (
        f"\n{APP_NAME}\n"
        "  1. Extract audio or video\n"
        "  2. Convert media\n"
        "  3. View media report\n"
        "  4. Remux all streams\n"
        "  5. Exit\n"
    )


def media_header(summary: dict[str, Any]) -> str:
    """Format the selected media file's summary for the console."""
    filename = Path(str(summary.get("filename") or "Unknown file")).name
    values = (
        f"MEDIA FILE: {filename}",
        f"FORMAT: {summary.get('format') or 'Unknown'}",
        f"DURATION: {summary.get('duration') or 'Unknown'} seconds",
        f"FILE SIZE: {summary.get('size') or 'Unknown'} bytes",
        (
            f"STREAMS: {summary.get('video_streams', 0)} video, "
            f"{summary.get('audio_streams', 0)} audio, "
            f"{summary.get('subtitle_streams', 0)} subtitle"
        ),
    )
    return _boxed_lines(values)


def _prompt_yes_no(prompt: str) -> bool:
    """Prompt until the user answers yes or no."""
    while True:
        answer = input(f"{prompt} (Y/N): ").strip().lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Please enter Y or N.")


def _select_extraction_stream(
    streams_by_type: dict[str, list[dict[str, Any]]],
) -> tuple[str, int] | None:
    """Prompt for an available stream type and ordinal index."""
    available_types = [
        stream_type
        for stream_type, streams in streams_by_type.items()
        if streams
    ]
    if not available_types:
        print("This file has no audio or video streams to extract.")
        return None

    print("Available streams:")
    for stream_type in available_types:
        streams = streams_by_type[stream_type]
        print(f"  {stream_type.title()}:")
        for index, stream in enumerate(streams):
            tags_value = stream.get("tags")
            tags = cast(dict[str, Any], tags_value) if isinstance(tags_value, dict) else {}
            title = str(tags.get("title") or "")
            label = f", {title}" if title else ""
            print(
                f"    {index}. {stream.get('codec_name', 'unknown')}"
                f"{label}"
            )

    result: tuple[str, int] | None = None
    stream_type = input(
        "Extract which type? (video/audio, or B to go back): "
    ).strip().lower()
    if stream_type == "b":
        return None
    if stream_type not in available_types:
        print("Choose one of the available stream types.")
    else:
        selected_index_text = input(
            "Select stream number (or B to go back): "
        ).strip()
        if selected_index_text.lower() != "b":
            try:
                selected_index = int(selected_index_text)
            except ValueError:
                print("Stream number must be an integer.")
            else:
                if 0 <= selected_index < len(streams_by_type[stream_type]):
                    result = stream_type, selected_index
                else:
                    print("That stream number is not available.")

    return result


def extract_media(media: MediaInspector) -> None:
    """Offer audio or video stream extraction for the selected media."""
    streams_by_type = {
        "video": media.extract_video_streams(),
        "audio": media.extract_audio_streams(),
    }
    selected = _select_extraction_stream(streams_by_type)
    if selected is None:
        return
    stream_type, selected_index = selected

    selected_stream = streams_by_type[stream_type][selected_index]
    filename = Path(str(media.get_summary().get("filename") or media.file_path)).stem
    try:
        Muxer(str(media.file_path)).muxing(
            stream_type,
            str(selected_stream.get("codec_name") or "copy"),
            filename,
            stream_index=selected_index,
        )
    except (FileExistsError, FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"Extraction failed: {error}")
    else:
        print(f"{stream_type.title()} extraction completed.")


def convert_media(media: MediaInspector) -> None:
    """Prompt for the stream selection and format, then transcode the file."""
    stream_choices: dict[str, Literal["video", "audio", "both"]] = {
        "1": "video",
        "2": "audio",
        "3": "both",
    }
    print("Transcode streams:")
    print("  1. Video only")
    print("  2. Audio only")
    print("  3. Video and audio")
    stream_choice = input("Select streams (or B to go back): ").strip().lower()
    if stream_choice == "b":
        return
    stream_mode = stream_choices.get(stream_choice)
    if stream_mode is None:
        print("Invalid stream selection.")
        return

    output_formats = (
        AUDIO_CONTAINER_FORMATS
        if stream_mode == "audio"
        else VIDEO_CONTAINER_FORMATS
    )
    print(f"Supported output formats: {', '.join(output_formats)}")
    output_format = input("Convert to format (or B to go back): ").strip().lower()
    if output_format == "b":
        return

    output_format = output_format.lstrip(".")
    if output_format not in output_formats:
        print(f"Unsupported format: {output_format}")
        return

    try:
        output_path = Transcoder(media.file_path).transcode(
            output_format,
            stream_mode=stream_mode,
        )
    except (FileExistsError, FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"Transcoding failed: {error}")
    else:
        print(f"Transcoding complete: {output_path}")


def remux_media(media: MediaInspector) -> None:
    """Copy all input streams into a supported output container."""
    print(f"Supported remux formats: {', '.join(REMUX_FORMATS)}")
    output_format = input("Remux to format (or B to go back): ").strip().lower()
    if output_format == "b":
        return

    output_format = output_format.lstrip(".")
    if output_format not in REMUX_FORMATS:
        print(f"Unsupported format: {output_format}")
        return

    try:
        output_path = Muxer(media.file_path).remuxing(output_format=output_format)
    except (FileExistsError, FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"Remux failed: {error}")
    else:
        print(f"Remux complete: {output_path}")


def _confirm_exit(media: MediaInspector) -> bool:
    """Confirm exit and optionally save the inspection report."""
    if not _prompt_yes_no("Exit the program?"):
        return False

    if _prompt_yes_no("Save the media inspection report before exiting?"):
        try:
            media.save_report()
        except (OSError, RuntimeError, ValueError) as error:
            print(f"Could not save the report: {error}")
            return False
        print("Report saved in the report directory.")

    return True


def main() -> int:
    """Run the interactive console application."""
    print(console_header())
    print("Choose a media file in the file picker.")

    try:
        file_path = open_files()
    except (OSError, RuntimeError) as error:
        print(f"Could not open the file picker: {error}")
        return 1

    if file_path is None:
        print("No file selected. Exiting.")
        return 0

    try:
        media = MediaInspector(file_path)
        summary = media.get_summary()
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"Could not inspect the selected media: {error}")
        return 1

    print("\nMedia summary:")
    print(media_header(summary))

    while True:
        print(app_menu())
        choice = input("Select an option: ").strip()

        if choice == "1":
            extract_media(media)
        elif choice == "2":
            convert_media(media)
        elif choice == "3":
            media.print_text_report()
        elif choice == "4":
            remux_media(media)
        elif choice == "5":
            if _confirm_exit(media):
                print("Goodbye.")
                return 0
        else:
            print("Invalid choice. Select 1, 2, 3, 4, or 5.")


def run() -> int:
    """Run the console app and translate an interrupted session into a clean exit."""
    try:
        return main()
    except (EOFError, KeyboardInterrupt):
        print("\nInput closed. Exiting.")
        return 0


if __name__ == "__main__":
    raise SystemExit(run())
