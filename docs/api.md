# Python API

The interactive console is the main interface. The classes below can also be
used from Python scripts.

## `MediaInspector`

Import from `media.media_inspector`.

```python
from media.media_inspector import MediaInspector

inspector = MediaInspector("input.mp4")
summary = inspector.get_summary()
report_data = inspector.save_report("report")
```

Useful methods:

- `get_media_details()` probes and caches FFprobe output.
- `get_summary()`, `get_format()`, `get_metadata()`, and `get_chapters()`
  return normalized media details.
- `extract_video_streams()`, `extract_audio_streams()`,
  `extract_subtitle_streams()`, `extract_data_streams()`, and
  `extract_attachment_streams()` return streams grouped by type.
- `print_text_report()` prints a readable report.
- `print_report()` prints the structured report as JSON text.
- `save_report(output_dir="report")` saves a uniquely named JSON report and
  returns the report data.

## `Transcoder`

Import from `deocder_main`.

```python
from deocder_main import Transcoder

output_path = Transcoder("input.mp4").transcode(
    "mkv",
    output_dir="converted",
    stream_mode="both",
    video_codec="libx264",
    audio_codec=None,
    overwrite=False,
)
```

`stream_mode` is `"video"`, `"audio"`, or `"both"`. Video and combined modes
accept MP4/MKV; audio-only accepts AAC/MP3. The output path is returned.

## `Muxer`

Import from `demuxer_main`.

```python
from demuxer_main import Muxer

muxer = Muxer("input.mp4")
remuxed_path = muxer.remuxing(output_format="mkv", output_dir="remuxed")
```

- `muxing(stream_type, codec_name, output_filename, output_dir="music",
  stream_index=0, overwrite=False)` copies one audio or video stream.
- `remuxing(output_filename=None, output_format="mkv",
  output_dir="remuxed", overwrite=False)` copies every source stream using
  FFmpeg's `-map 0`.

In both operations, output files are not overwritten unless
`overwrite=True`. Remux success depends on destination-container support for
all copied streams.
