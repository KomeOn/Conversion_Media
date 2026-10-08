"""Application labels and supported media container formats."""

APP_NAME = "Local convertor"
DESCRIPTION = (
    "Local convertor module to extract, encode, and decode media files "
    "to another format using FFmpeg."
)
VIDEO_CONTAINER_FORMATS = ("mp4", "mkv")
AUDIO_CONTAINER_FORMATS = ("aac", "mp3")
SUPPORTED_FORMAT = [*VIDEO_CONTAINER_FORMATS, *AUDIO_CONTAINER_FORMATS]
REMUX_FORMATS = VIDEO_CONTAINER_FORMATS
TERMS_CONDITIONS = "Licensed under GNU GPL v3.0"
