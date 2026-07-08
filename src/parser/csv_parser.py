from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd

from src.parser.section_mapper import canonical_section


def _read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def dataframe_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    df = df.dropna(how="all")
    df.columns = [str(col).strip() for col in df.columns]
    df = df.fillna("")
    return df.to_dict(orient="records")


def parse_csv_text(text: str) -> list[dict[str, Any]]:
    if not text.strip():
        return []
    dataframe = pd.read_csv(StringIO(text), sep=None, engine="python")
    return dataframe_to_records(dataframe)


def parse_csv_file(path: str | Path) -> list[dict[str, Any]]:
    file_path = Path(path)
    return parse_csv_text(_read_text(file_path))


def parse_csv_sections(paths: list[str | Path]) -> dict[str, list[dict[str, Any]]]:
    sections: dict[str, list[dict[str, Any]]] = {}
    for path in paths:
        file_path = Path(path)
        section = canonical_section(file_path.stem.replace("_", " "))
        try:
            rows = parse_csv_file(file_path)
        except Exception:
            rows = []
        if rows:
            sections.setdefault(section, []).extend(rows)
    return sections
