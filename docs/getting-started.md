# Getting Started

## Prerequisites

Install Python 3.10 or newer, then install FFmpeg with FFprobe and make both
commands available on your `PATH`.

The graphical file picker also needs a desktop session and platform-specific
support:

| Platform | Picker |
| --- | --- |
| Windows | PowerShell and Windows Forms |
| macOS | `osascript` |
| Linux | Zenity or KDialog; Tkinter is the fallback |
| WSL | Windows PowerShell picker and `wslpath` |

## Install Python dependencies

From the repository root:

```bash
python -m pip install -r requirements.txt
```

## Run the application

```bash
python app_main.py
```

Choose a media file in the picker. The application probes it and displays a
summary before showing the operations menu.

## Run tests

The complete suite includes unit tests and real FFmpeg integration tests:

```bash
python -m pytest -q tests
```

Run only tests that invoke real FFmpeg and FFprobe:

```bash
python -m pytest -q tests/test_media_integration.py
```

The integration tests generate short synthetic media under pytest's temporary
directory; they do not process or modify your media library.

To produce the configured JUnit result as well:

```bash
bash tests/run_tests.sh
```
