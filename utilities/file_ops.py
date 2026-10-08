"""Cross-platform native file-picker helpers."""

from importlib import import_module
import shutil
import subprocess

from path_helper import to_wsl_path
from utilities.platform_name import platform_system


def is_wsl() -> bool:
    """Return True if Python is running inside WSL."""
    if platform_system() != "Linux":
        return False

    try:
        with open("/proc/version", "r", encoding="utf-8") as file:
            version = file.read().lower()
        return "microsoft" in version or "wsl" in version
    except FileNotFoundError:
        return False


def windows_file_picker() -> str | None:
    """Open the native Windows file picker."""

    powershell = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
    if not powershell:
        raise RuntimeError(
            "PowerShell was not found. "
            "Make sure Windows executables are accessible from WSL."
        )

    script = r"""
Add-Type -AssemblyName System.Windows.Forms

$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Title = "Select a file"

if ($dialog.ShowDialog() -eq "OK") {
    Write-Output $dialog.FileName
}
"""

    result = subprocess.run(
        [powershell, "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    path = result.stdout.strip()
    return path or None


def linux_file_picker() -> str | None:
    """Open a Linux native file picker or a tkinter fallback."""

    for command, args in (
        ("zenity", ["--file-selection"]),
        ("kdialog", ["--getopenfilename"]),
    ):
        executable = shutil.which(command)
        if not executable:
            continue

        result = subprocess.run(
            [executable, *args],
            capture_output=True,
            text=True,
            check=False,
        )

        path = result.stdout.strip()
        if result.returncode == 0 and path:
            return path

    try:
        tk = import_module("tkinter")
        filedialog = import_module("tkinter.filedialog")
    except ImportError as error:
        raise RuntimeError(
            "No Linux file picker found. "
            "Install 'zenity' or 'kdialog', or install tkinter and run this "
            "app in a desktop session."
        ) from error

    root = tk.Tk()
    root.withdraw()
    try:
        path = filedialog.askopenfilename(title="Select a media file")
    except tk.TclError as error:
        raise RuntimeError(
            "Could not open a Linux file picker. Run this app in a desktop session."
        ) from error
    finally:
        root.destroy()

    return path or None


def macos_file_picker() -> str | None:
    """Open the native macOS file picker."""

    script = 'POSIX path of (choose file with prompt "Select a file")'
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        return None

    path = result.stdout.strip()
    return path or None


def open_files() -> str | None:
    """Open a platform-native file-selection dialog and return the selected path."""

    system = platform_system()

    if system == "Windows":
        return windows_file_picker()

    if system == "Linux":
        if is_wsl():
            windows_path = windows_file_picker()
            if windows_path is None:
                return None
            return to_wsl_path(windows_path)
        return linux_file_picker()

    if system == "Darwin":
        return macos_file_picker()

    raise RuntimeError(f"Unsupported operating system: {system}")
