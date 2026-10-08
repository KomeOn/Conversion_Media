"""Shared helpers for reporting FFmpeg errors."""

import ffmpeg


def get_error_details(error: ffmpeg.Error) -> str:
    """Return FFmpeg's stderr as readable text."""
    stderr = error.stderr
    if isinstance(stderr, bytes):
        return stderr.decode("utf-8", errors="replace")
    return str(stderr or "")
