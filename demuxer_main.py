"""Media stream extraction and container remuxing via FFmpeg."""

from pathlib import Path
from typing import Any, cast

import ffmpeg

from fixed_values.constants import REMUX_FORMATS
from utilities.ffmpeg_utils import get_error_details


class Muxer:
    """Extract individual streams or copy streams into another container."""

    def __init__(self, file_path: str | Path):
        self.media = Path(file_path)

    @staticmethod
    def _validate_output_path(
        source: Path,
        output_path: Path,
        overwrite: bool,
    ) -> None:
        """Validate an output target before starting FFmpeg."""
        if source.resolve() == output_path.resolve():
            raise ValueError("Output path must be different from the input file")
        if output_path.exists() and not overwrite:
            raise FileExistsError(f"Output file already exists: {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _run(command: Any, operation: str) -> None:
        """Run an FFmpeg command and provide its stderr on failure."""
        try:
            command.run()
        except ffmpeg.Error as error:
            raise RuntimeError(
                f"FFmpeg failed to {operation}:\n{get_error_details(error)}"
            ) from error

    def _demuxing(
        self,
        stream_type: str,
        stream_index: int,
        output_path: Path,
        overwrite: bool,
    ) -> Path:
        """Extract one selected audio or video stream without re-encoding."""
        try:
            source = cast(Any, ffmpeg).input(str(self.media))
            stream = source[f"{stream_type[0]}:{stream_index}"]
            codec_option = "vcodec" if stream_type == "video" else "acodec"
            command = cast(Any, ffmpeg).output(
                stream,
                str(output_path),
                **{codec_option: "copy"},
            )
            if overwrite:
                command = command.overwrite_output()
            else:
                command = command.global_args("-n")
        except ffmpeg.Error as error:
            raise RuntimeError(
                f"FFmpeg failed to prepare {stream_type} extraction:\n"
                f"{get_error_details(error)}"
            ) from error

        self._run(command, f"extract {stream_type} from {self.media}")
        return output_path

    def _remuxing(
        self,
        output_path: Path,
        overwrite: bool,
    ) -> Path:
        """Copy all streams from the source into a different container."""
        try:
            source = cast(Any, ffmpeg).input(str(self.media))
            command = cast(Any, ffmpeg).output(
                source,
                str(output_path),
                codec="copy",
                map="0",
            )
            if overwrite:
                command = command.overwrite_output()
            else:
                command = command.global_args("-n")
        except ffmpeg.Error as error:
            raise RuntimeError(
                f"FFmpeg failed to prepare remux:\n{get_error_details(error)}"
            ) from error

        self._run(command, f"remux {self.media} to {output_path}")
        return output_path

    # These explicit output controls are part of the existing public API.
    # pylint: disable=too-many-arguments
    def muxing(
        self,
        stream_type: str,
        codec_name: str,
        output_filename: str,
        output_dir: str | Path = "music",
        *,
        stream_index: int = 0,
        overwrite: bool = False,
    ) -> Path:
        """Extract a single audio or video stream without re-encoding."""
        if not self.media.is_file():
            raise FileNotFoundError(f"Input media file does not exist: {self.media}")
        if stream_type not in {"video", "audio"}:
            raise ValueError(f"Unsupported stream type: {stream_type}")
        if not codec_name or Path(codec_name).name != codec_name:
            raise ValueError("A valid codec name is required")
        if not output_filename or Path(output_filename).name != output_filename:
            raise ValueError("Output filename must be a non-empty filename")
        if stream_index < 0:
            raise ValueError("Stream index must be zero or greater")
        output_path = Path(output_dir) / f"{output_filename}.{codec_name}"
        self._validate_output_path(self.media, output_path, overwrite)

        return self._demuxing(
            stream_type=stream_type,
            stream_index=stream_index,
            output_path=output_path,
            overwrite=overwrite,
        )

    # pylint: enable=too-many-arguments
    def remuxing(
        self,
        output_filename: str | None = None,
        output_format: str = "mkv",
        output_dir: str | Path = "remuxed",
        *,
        overwrite: bool = False,
    ) -> Path:
        """Copy every stream into another supported container without encoding."""
        if not self.media.is_file():
            raise FileNotFoundError(f"Input media file does not exist: {self.media}")

        normalized_format = output_format.lower().lstrip(".")
        if normalized_format not in REMUX_FORMATS:
            raise ValueError(
                f"Unsupported output format {normalized_format!r}. "
                f"Supported remux formats: {', '.join(REMUX_FORMATS)}"
            )
        name = output_filename or self.media.stem
        if Path(name).name != name:
            raise ValueError("Output filename must be a filename, not a path")

        output_path = Path(output_dir) / f"{name}.{normalized_format}"
        self._validate_output_path(self.media, output_path, overwrite)

        return self._remuxing(
            output_path=output_path,
            overwrite=overwrite,
        )
