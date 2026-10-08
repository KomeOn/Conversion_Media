"""Shared media report rendering and persistence utilities."""

import json
from pathlib import Path
from typing import Any

from media.utility_functions import report as text_report


class PrintMedia:
    """Helpers for rendering and persisting media inspection reports."""

    @staticmethod
    def _as_json(data: Any, *, indent: int = 2) -> str:
        return json.dumps(data, indent=indent, ensure_ascii=False)

    def print_json_report(self, report: dict[str, Any], *, indent: int = 2) -> str:
        """Print a complete media report."""
        content = self._as_json(report, indent=indent)
        print(content)
        return content

    def save_json_report(
        self,
        report: dict[str, Any],
        output_dir: str | Path = "report",
        file_name: str | None = None,
    ) -> Path:
        """Write a JSON representation of the report to disk and return its path."""
        report_dir = Path(output_dir)
        report_dir.mkdir(parents=True, exist_ok=True)

        if file_name is None:
            file_name = "media_report.json"

        report_path = report_dir / file_name
        with report_path.open("w", encoding="utf-8") as report_file:
            json.dump(report, report_file, indent=2, ensure_ascii=False)

        return report_path

    def print_readable_report(
        self,
        report: dict[str, Any],
        file_path: str,
    ) -> str:
        """Render the human-readable report using the shared formatter helpers."""
        text = text_report(report, file_path)
        print(text)
        return text
