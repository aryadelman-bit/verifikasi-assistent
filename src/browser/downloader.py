from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


def safe_slug(value: str, fallback: str = "item") -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    slug = re.sub(r"_+", "_", slug).strip("._")
    return slug[:120] or fallback


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_text(text: str, directory: str | Path, name: str, suffix: str = ".html") -> Path:
    folder = Path(directory)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{timestamp()}_{safe_slug(name)}{suffix}"
    path.write_text(text, encoding="utf-8")
    return path


def save_bytes(data: bytes, directory: str | Path, name: str, suffix: str = ".csv") -> Path:
    folder = Path(directory)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{timestamp()}_{safe_slug(name)}{suffix}"
    path.write_bytes(data)
    return path

