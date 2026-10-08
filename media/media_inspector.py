"""Probe media files and build structured or readable inspection reports."""

from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import ffmpeg

from media.print_media_report import PrintMedia
from utilities.ffmpeg_utils import get_error_details


class MediaInspector(PrintMedia):
    """Inspect media files with FFprobe."""

    def __init__(self, file_path: str | Path):
        super().__init__()
        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(f"File does not exist: {self.file_path}")
        if not self.file_path.is_file():
            raise ValueError(f"Input path is not a file: {self.file_path}")

        self.probed_media: dict[str, Any] = {}

    def get_media_details(self) -> dict[str, Any]:
        """Probe and cache stream and format details for the input file."""
        if self.probed_media:
            return self.probed_media

        try:
            self.probed_media = ffmpeg.probe(filename=str(self.file_path))
        except ffmpeg.Error as error:
            raise RuntimeError(
                f"FFprobe failed for {self.file_path}:\n"
                f"{get_error_details(error)}"
            ) from error

        return self.probed_media

    def get_summary(self) -> dict[str, Any]:
        """Return a compact summary of the input media."""
        format_info = self._format_info()
        return {
            "filename": format_info.get("filename"),
            "format": format_info.get("format_name"),
            "format_long_name": format_info.get("format_long_name"),
            "duration": format_info.get("duration"),
            "size": format_info.get("size"),
            "bit_rate": format_info.get("bit_rate"),
            "video_streams": len(self.extract_video_streams()),
            "audio_streams": len(self.extract_audio_streams()),
            "subtitle_streams": len(self.extract_subtitle_streams()),
        }

    def get_format(self) -> dict[str, Any]:
        """Return normalized container-format details."""
        return self._extract_media_format()

    def get_metadata(self) -> dict[str, Any]:
        """Return container-level metadata tags."""
        return self._extract_metadata()

    def get_chapters(self) -> list[dict[str, Any]]:
        """Return chapter entries, or an empty list when none are present."""
        chapters = self.get_media_details().get("chapters", [])
        return cast(list[dict[str, Any]], chapters) if isinstance(chapters, list) else []

    def _format_info(self) -> dict[str, Any]:
        return self.get_media_details()["format"]

    def _streams_info(self) -> list[dict[str, Any]]:
        return self.get_media_details()["streams"]

    def _extract_metadata(self) -> dict[str, Any]:
        return self._format_info().get("tags", {})

    def _extract_media_format(self) -> dict[str, Any]:
        format_info = self._format_info()
        format_names = format_info.get("format_name") or ""
        return {
            "Filename": format_info.get("filename", ""),
            "Format Names": format_names.split(","),
            "Stream Count": format_info.get("nb_streams", 0),
            "Duration": format_info.get("duration", 0),
            "Creation Time": format_info.get("tags", {}).get("creation_time", 0),
        }

    def _extract_streams(self, codec_type: str) -> list[dict[str, Any]]:
        return [
            stream
            for stream in self._streams_info()
            if stream.get("codec_type") == codec_type
        ]

    def extract_audio_streams(self) -> list[dict[str, Any]]:
        """Return audio stream information."""
        return self._extract_streams("audio")

    def extract_video_streams(self) -> list[dict[str, Any]]:
        """Return video stream information."""
        return self._extract_streams("video")

    def extract_subtitle_streams(self) -> list[dict[str, Any]]:
        """Return subtitle stream information."""
        return self._extract_streams("subtitle")

    def extract_data_streams(self) -> list[dict[str, Any]]:
        """Return data stream information."""
        return self._extract_streams("data")

    def extract_attachment_streams(self) -> list[dict[str, Any]]:
        """Return embedded attachment stream information."""
        return self._extract_streams("attachment")

    def _build_report(self) -> dict[str, Any]:
        return {
            "Summary": self.get_summary(),
            "Video": self.extract_video_streams(),
            "Audio": self.extract_audio_streams(),
            "Subtitle": self.extract_subtitle_streams(),
            "Data": self.extract_data_streams(),
            "Attachment": self.extract_attachment_streams(),
            "Metadata": self.get_metadata(),
            "Chapters": self.get_chapters(),
        }

    def save_report(self, output_dir: str | Path = "report") -> dict[str, Any]:
        """Write a JSON report and return the report data."""
        data = self._build_report()
        file_name = (
            f"{self.file_path.stem}_{self.file_path.suffix.lstrip('.')}_"
            f"{uuid4().hex}.json"
        )
        self.save_json_report(data, output_dir=output_dir, file_name=file_name)
        return data

    def print_report(self) -> None:
        """Print the report as formatted JSON without writing a file."""
        self.print_json_report(self._build_report())

    def print_text_report(self) -> str:
        """Render and print the human-readable media report using the shared formatter helpers."""
        report_data = self._build_report()
        return self.print_readable_report(report_data, str(self.file_path))
