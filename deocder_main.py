"""Transcode audio and video streams with FFmpeg."""

from pathlib import Path
from typing import Any, Literal, cast

import ffmpeg

from fixed_values.constants import (
    AUDIO_CONTAINER_FORMATS,
    SUPPORTED_FORMAT,
    VIDEO_CONTAINER_FORMATS,
)
from utilities.ffmpeg_utils import get_error_details


class Transcoder:
    """Transcode media streams into a supported container format."""

    def __init__(self, file_path: str | Path):
        """Initialize a transcoder for one input media file."""
        self.media = Path(file_path)

    @property
    def input_path(self) -> Path:
        """Return the source media path."""
        return self.media

    def _validate_request(
        self,
        output_path: Path,
        output_format: str,
        stream_mode: Literal["video", "audio", "both"],
        video_codec: str,
        audio_codec: str | None,
    ) -> str:
        """Validate the requested output path, streams, and codecs."""
        if output_format not in SUPPORTED_FORMAT:
            raise ValueError(
                f"Unsupported output format {output_format!r}. "
                f"Supported formats: {', '.join(SUPPORTED_FORMAT)}"
            )
        if not self.media.is_file():
            raise FileNotFoundError(f"Input media file does not exist: {self.media}")
        if stream_mode not in {"video", "audio", "both"}:
            raise ValueError(
                "stream_mode must be 'video', 'audio', or 'both'"
            )
        if stream_mode in {"video", "both"} and output_format not in VIDEO_CONTAINER_FORMATS:
            raise ValueError(
                f"{output_format!r} cannot contain the selected video stream mode"
            )
        if stream_mode == "audio" and output_format not in AUDIO_CONTAINER_FORMATS:
            raise ValueError(
                f"Audio-only output must use one of: "
                f"{', '.join(AUDIO_CONTAINER_FORMATS)}"
            )
        if stream_mode in {"video", "both"} and not video_codec:
            raise ValueError("Video codec must be a non-empty string")
        if stream_mode in {"audio", "both"} and audio_codec == "":
            raise ValueError("Audio codec must be a non-empty string")
        if self.media.resolve() == output_path.resolve():
            raise ValueError("Output path must be different from the input file")
        return output_format

    def _check_required_streams(
        self,
        stream_mode: Literal["video", "audio", "both"],
    ) -> None:
        """Raise when the input lacks a stream required by the selected mode."""
        probe = cast(Any, ffmpeg).probe(str(self.media))
        stream_types = {
            stream.get("codec_type")
            for stream in probe.get("streams", [])
        }
        required_types = (
            {"video"}
            if stream_mode == "video"
            else {"audio"}
            if stream_mode == "audio"
            else {"video", "audio"}
        )
        missing_types = required_types - stream_types
        if missing_types:
            missing = ", ".join(sorted(missing_types))
            raise ValueError(f"Input file does not contain required stream(s): {missing}")

    def _build_command(
        self,
        output_path: Path,
        output_format: str,
        stream_mode: Literal["video", "audio", "both"],
        video_codec: str,
        audio_codec: str | None,
    ) -> Any:
        """Build an FFmpeg command mapping all selected streams."""
        source = cast(Any, ffmpeg).input(str(self.media))
        selected_streams: list[Any] = []
        output_options: dict[str, str | None] = {}
        if stream_mode in {"video", "both"}:
            output_options["vcodec"] = video_codec
            selected_streams.append(source.video)
        if stream_mode in {"audio", "both"}:
            audio_codec_name = audio_codec or (
                "libmp3lame" if output_format == "mp3" else "aac"
            )
            output_options["acodec"] = audio_codec_name
            selected_streams.append(source.audio)
        if stream_mode == "video":
            output_options["an"] = None
        elif stream_mode == "audio":
            output_options["vn"] = None
        return cast(Any, ffmpeg).output(
            *selected_streams, str(output_path), **output_options
        )

    # The conversion options are explicit to keep the public API type-safe.
    # pylint: disable=too-many-arguments
    def transcode(
        self,
        output_format: str,
        output_dir: str | Path = "converted",
        *,
        stream_mode: Literal["video", "audio", "both"] = "both",
        video_codec: str = "libx264",
        audio_codec: str | None = None,
        overwrite: bool = False,
    ) -> Path:
        """Transcode selected streams and return the generated output path."""
        output_format = output_format.lower().lstrip(".")
        output_dir = Path(output_dir)
        output_path = output_dir / f"{self.media.stem}.{output_format}"
        output_format = self._validate_request(
            output_path, output_format, stream_mode, video_codec, audio_codec
        )
        if output_path.exists() and not overwrite:
            raise FileExistsError(f"Output file already exists: {output_path}")

        try:
            self._check_required_streams(stream_mode)
            output_dir.mkdir(parents=True, exist_ok=True)
            command = self._build_command(
                output_path, output_format, stream_mode, video_codec, audio_codec
            )
            if overwrite:
                command = command.overwrite_output()
            else:
                command = command.global_args("-n")
            command.run()
        except ffmpeg.Error as error:
            raise RuntimeError(
                f"FFmpeg failed to transcode {self.media} to {output_path}:\n"
                f"{get_error_details(error)}"
            ) from error

        return output_path
