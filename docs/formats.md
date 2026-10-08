# Formats and Outputs

The interactive menu and the APIs enforce these format groups:

| Operation | Supported formats | Behavior |
| --- | --- | --- |
| Video-only transcode | MP4, MKV | Re-encodes video; omits audio |
| Audio-only transcode | AAC, MP3 | Re-encodes audio; omits video |
| Combined audio/video transcode | MP4, MKV | Re-encodes selected video and audio streams |
| Remux | MP4, MKV | Copies all streams without re-encoding |
| Stream extraction | Source codec extension | Copies one selected audio or video stream |

The selected container format does not guarantee that arbitrary codecs or
streams will be compatible. FFmpeg reports an error if it cannot create the
requested output.

## Default output folders

| Result | Folder |
| --- | --- |
| Transcoded media | `converted/` |
| Extracted streams | `music/` |
| Remuxed media | `remuxed/` |
| Saved JSON reports | `report/` |

Folders are relative to the current working directory and are created when
the operation runs. The application does not create every folder at startup.
