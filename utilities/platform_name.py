"""Helpers for identifying the current operating system."""

import platform


def platform_system() -> str:
    """Return the current platform name, such as ``Linux`` or ``Windows``."""
    return platform.system()
