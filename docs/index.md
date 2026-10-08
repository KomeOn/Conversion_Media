# Local Convertor

**A local Python/FFmpeg console app for inspecting, extracting, transcoding,
and remuxing media.**

Local Convertor works with files on your computer. It uses FFprobe to inspect
media and FFmpeg to process selected audio and video streams.

## What you can do

- Inspect media streams, format details, metadata, and chapters.
- Extract a selected audio or video stream without re-encoding.
- Transcode video, audio, or both to supported formats.
- Remux streams into another container without re-encoding.
- Display readable reports or save a JSON report.

## Start here

- [Install and run the application](getting-started.md)
- [Learn the interactive workflow](user-guide.md)
- [Check supported formats and output folders](formats.md)
- [Run tests or contribute](development.md)

## Requirements at a glance

- Python 3.10 or later.
- FFmpeg and FFprobe available on `PATH`.
- A desktop session and a file picker supported by your operating system.

The file picker uses native tools: PowerShell on Windows, AppleScript on
macOS, and Zenity/KDialog or Tkinter on Linux. Under WSL, it uses the Windows
picker and converts the selected path.

## Important limitations

- Remuxing copies every input stream. It may fail when a destination
  container cannot store one of the selected streams.
- Real FFmpeg integration tests require FFmpeg and FFprobe; the regular unit
  tests mock FFmpeg calls.
- Cross-platform operation depends on the external tools and file picker
  being installed and has not been verified on every operating system.

See the [user guide](user-guide.md) and [development notes](development.md)
for details.
