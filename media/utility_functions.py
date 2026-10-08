"""Formatting helpers for human-readable media inspection reports."""

from typing import Any, cast


def _stream_tags(stream: dict[str, Any]) -> dict[str, Any]:
    """Return stream tags when FFprobe provides them as a mapping."""
    tags = stream.get("tags")
    return cast(dict[str, Any], tags) if isinstance(tags, dict) else {}


def format_duration(seconds: str | float | None) -> str:
    """Convert seconds into HH:MM:SS.mmm format."""

    if seconds is None:
        return "-"

    total_seconds = float(seconds)
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    remaining = total_seconds % 60

    return f"{hours:02d}:{minutes:02d}:{remaining:06.3f}"


def format_bitrate(bitrate: str | int | None) -> str:
    """Convert bitrate from bits/sec to kb/s."""

    if bitrate is None:
        return "-"

    return f"{int(bitrate) / 1000:.2f} kb/s"


def format_size(size: str | int | None) -> str:
    """Convert bytes into a human-readable size."""

    if size is None:
        return "-"

    size = int(size)
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)

    for unit in units:
        if value < 1024:
            return f"{value:.2f} {unit}"
        value /= 1024

    return f"{value:.2f} PB"


def format_frame_rate(frame_rate: str | None) -> str:
    """Convert an FFmpeg frame-rate fraction into approximate FPS."""

    if not frame_rate or frame_rate in {"0/0", "N/A"}:
        return "-"

    try:
        numerator, denominator = frame_rate.split("/")
        fps = int(numerator) / int(denominator)
        return f"{fps:.2f} fps"
    except (ValueError, ZeroDivisionError):
        return frame_rate


def format_subtitle_stream(stream: dict[str, Any]) -> dict[str, Any]:
    """Normalize subtitle metadata into a simple printable structure."""

    tags = _stream_tags(stream)
    return {
        "index": stream.get("index", "-"),
        "codec": stream.get("codec_name", "-"),
        "language": tags.get("language", "-"),
        "title": tags.get("title", "-"),
    }


def format_video_stream(stream: dict[str, Any]) -> dict[str, Any]:
    """Normalize an FFprobe video stream for the readable report."""
    tags = _stream_tags(stream)
    width = stream.get("width")
    height = stream.get("height")
    resolution = f"{width}x{height}" if width and height else "-"
    return {
        "index": stream.get("index", "-"),
        "codec": stream.get("codec_name", "-"),
        "profile": stream.get("profile"),
        "resolution": resolution,
        "frame_rate": format_frame_rate(
            stream.get("avg_frame_rate") or stream.get("r_frame_rate")
        ),
        "pixel_format": stream.get("pix_fmt"),
        "bitrate": format_bitrate(stream.get("bit_rate")),
        "language": tags.get("language", "-"),
        "title": tags.get("title", "-"),
    }


def format_audio_stream(stream: dict[str, Any]) -> dict[str, Any]:
    """Normalize an FFprobe audio stream for the readable report."""
    tags = _stream_tags(stream)
    sample_rate = stream.get("sample_rate")
    return {
        "index": stream.get("index", "-"),
        "codec": stream.get("codec_name", "-"),
        "profile": stream.get("profile"),
        "channels": stream.get("channels"),
        "channel_layout": stream.get("channel_layout"),
        "sample_rate": f"{sample_rate} Hz" if sample_rate else "-",
        "bitrate": format_bitrate(stream.get("bit_rate")),
        "language": tags.get("language", "-"),
        "title": tags.get("title", "-"),
    }


def _append_video_section(
    lines: list[str],
    videos: list[dict[str, Any]],
) -> None:
    """Append normalized video stream details to the report."""
    lines.extend(("", "Video Streams", "-" * 60))
    if not videos:
        lines.append("None")
    for stream in videos:
        data = format_video_stream(stream)
        lines.extend(
            (
                "",
                f"[Video #{data['index']}]",
                f"Codec       : {data['codec']}",
                f"Profile     : {data['profile'] or '-'}",
                f"Resolution  : {data['resolution']}",
                f"Frame Rate  : {data['frame_rate']}",
                f"Pixel Format: {data['pixel_format'] or '-'}",
                f"Bitrate     : {data['bitrate']}",
                f"Language    : {data['language']}",
                f"Title       : {data['title']}",
            )
        )


def _append_audio_section(
    lines: list[str],
    audios: list[dict[str, Any]],
) -> None:
    """Append normalized audio stream details to the report."""
    lines.extend(("", "Audio Streams", "-" * 60))
    if not audios:
        lines.append("None")
    for stream in audios:
        data = format_audio_stream(stream)
        lines.extend(
            (
                "",
                f"[Audio #{data['index']}]",
                f"Codec       : {data['codec']}",
                f"Profile     : {data['profile'] or '-'}",
                f"Channels    : {data['channels'] or '-'}",
                f"Layout      : {data['channel_layout'] or '-'}",
                f"Sample Rate : {data['sample_rate']}",
                f"Bitrate     : {data['bitrate']}",
                f"Language    : {data['language']}",
                f"Title       : {data['title']}",
            )
        )


def _append_subtitle_section(
    lines: list[str],
    subtitles: list[dict[str, Any]],
) -> None:
    """Append normalized subtitle stream details to the report."""
    lines.extend(("", "Subtitle Streams", "-" * 60))
    if not subtitles:
        lines.append("None")
    for stream in subtitles:
        data = format_subtitle_stream(stream)
        lines.extend(
            (
                "",
                f"[Subtitle #{data['index']}]",
                f"Codec       : {data['codec']}",
                f"Language    : {data['language']}",
                f"Title       : {data['title']}",
            )
        )


def _append_metadata_section(lines: list[str], metadata: dict[str, Any]) -> None:
    """Append metadata tags to the report."""
    lines.extend(("", "Metadata", "-" * 60))
    if not metadata:
        lines.append("None")
    else:
        lines.extend(f"{key:<20}: {value}" for key, value in metadata.items())


def report(report_data: dict[str, Any], file_path: str) -> str:
    """Build a readable text report from a structured inspector report."""
    summary_value = report_data.get("Summary")
    summary = (
        cast(dict[str, Any], summary_value)
        if isinstance(summary_value, dict)
        else {}
    )
    metadata_value = report_data.get("Metadata")
    metadata = (
        cast(dict[str, Any], metadata_value)
        if isinstance(metadata_value, dict)
        else {}
    )
    videos = cast(list[dict[str, Any]], report_data.get("Video") or [])
    audios = cast(list[dict[str, Any]], report_data.get("Audio") or [])
    subtitles = cast(list[dict[str, Any]], report_data.get("Subtitle") or [])

    lines = [
        "=" * 60,
        "MEDIA INFORMATION",
        "=" * 60,
        "",
        "File",
        "-" * 60,
        f"Name        : {file_path}",
        f"Format      : {summary.get('format_long_name') or summary.get('format') or '-'}",
        f"Duration    : {format_duration(summary.get('duration'))}",
        f"Size        : {format_size(summary.get('size'))}",
        f"Bitrate     : {format_bitrate(summary.get('bit_rate'))}",
    ]
    _append_video_section(lines, videos)
    _append_audio_section(lines, audios)
    _append_subtitle_section(lines, subtitles)
    _append_metadata_section(lines, metadata)
    lines.extend(("", "=" * 60))
    return "\n".join(lines)
