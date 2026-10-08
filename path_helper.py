"""Convert filesystem paths between Windows and WSL formats."""

import subprocess


def _convert_path(path: str, option: str, direction: str) -> str:
    """Run wslpath and return its converted path."""
    if not path:
        raise ValueError("Path must not be empty")

    try:
        result = subprocess.run(
            ["wslpath", option, path],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as error:
        raise RuntimeError(
            "wslpath was not found; path conversion is available inside WSL."
        ) from error
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or "").strip()
        message = f"Unable to convert path to {direction}"
        if detail:
            message = f"{message}: {detail}"
        raise RuntimeError(message) from error

    converted_path = result.stdout.rstrip("\r\n")
    if not converted_path:
        raise RuntimeError(f"wslpath returned an empty {direction} path")
    return converted_path


def to_wsl_path(win_path: str) -> str:
    """Convert a Windows path to its WSL representation."""
    return _convert_path(win_path, "-u", "WSL")


def to_win_path(wsl_path: str) -> str:
    """Convert a WSL path to its Windows representation."""
    return _convert_path(wsl_path, "-w", "Windows")
