# User Guide

When the application starts, select a media file in the platform file picker.
After the media summary is shown, use the numbered menu.

## Extract audio or video

Choose the extraction option, select `video` or `audio`, then choose a
zero-based stream number from the list. The selected stream is copied without
re-encoding. The output extension is based on the stream codec; not all
codecs are standalone playable file formats.

## Convert media

Select one of:

- **Video only** — transcode the video stream and omit audio.
- **Audio only** — transcode the audio stream and omit video.
- **Video and audio** — transcode one video stream and one audio stream.

Then enter one of the formats listed by the application. The defaults are
H.264 (`libx264`) for video and AAC for audio, except MP3 output uses
`libmp3lame`.

## View a report

Choose the report option to display the readable summary, including stream
details and metadata.

## Remux

Remuxing copies all streams (`-map 0`) into the selected container and does
not re-encode them. The process is generally fast and does not introduce
generation loss, but it can fail when any stream is unsupported by the target
container.

## Exit and save

Choose Exit and confirm. The application then asks whether to save an
inspection report. A saved report is JSON and has a unique filename.

## Output behavior

Outputs are written relative to the directory from which the program is run.
Existing output files are not overwritten by default. The folders are created
when needed, not at startup. See [Formats and Outputs](formats.md).
