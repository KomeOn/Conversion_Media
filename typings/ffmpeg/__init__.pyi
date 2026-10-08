from typing import Any


class Error(Exception):
    stderr: bytes | None


def probe(filename: str, cmd: str = ..., **kwargs: Any) -> dict[str, Any]: ...
