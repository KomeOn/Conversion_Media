# Development and Tests

## Project layout

```text
.
├── app_main.py                 # Application entry point
├── file_main.py                # Interactive console workflow
├── deocder_main.py             # Audio/video transcoding
├── demuxer_main.py             # Stream extraction and remuxing
├── path_helper.py              # Windows/WSL path conversions
├── fixed_values/constants.py   # Format groups and application labels
├── media/                      # Probing and report rendering
├── utilities/                  # Picker, platform, and FFmpeg helpers
├── tests/                      # Unit and integration tests
├── docs/                       # MkDocs pages
└── mkdocs.yml                  # Docs site configuration
```

## Test levels

Run all tests:

```bash
python -m pytest -q tests
```

The unit tests use temporary inputs and mock external FFmpeg calls. The
integration tests create a real sample with FFmpeg, then verify probing,
report persistence, transcoding, remuxing, and the output streams through
FFprobe. Integration tests require both executables on `PATH`.

## Build the documentation locally

Install documentation dependencies and build a strict site:

```bash
python -m pip install -r requirements-docs.txt
mkdocs build --strict
```

Preview it locally with automatic reload:

```bash
mkdocs serve
```

Then open <http://127.0.0.1:8000>.

## Contributing checks

Before submitting a change, run the tests and build the documentation:

```bash
python -m pytest -q tests
mkdocs build --strict
```

Keep generated site output (`site/`), test results, converted media, and
personal reports out of commits.
