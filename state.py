"""Small, atomic JSON state store used to prevent duplicate alerts."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"openings": {}}
    try:
        raw = path.read_text().strip()
        if not raw:
            return {"openings": {}}
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"State file is not valid JSON: {path}") from exc
    if not isinstance(data.get("openings"), dict):
        raise RuntimeError(f"State file has no openings object: {path}")
    return data


def save_state(path: Path, openings: dict[str, dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps({"openings": openings}, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)
