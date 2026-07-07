from __future__ import annotations

import re
from typing import Any, Iterable

from src.parser.number_normalizer import normalize_number, to_float


def canonical_key(text: Any) -> str:
    normalized = str(text or "").strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_")


def section(report: dict[str, Any], *names: str) -> list[dict[str, Any]]:
    sections = report.get("sections", {}) or {}
    for name in names:
        value = sections.get(name)
        if value is None:
            continue
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
        if isinstance(value, dict):
            rows = value.get("rows")
            if isinstance(rows, list):
                return [row for row in rows if isinstance(row, dict)]
            return [value]
    return []


def metadata(report: dict[str, Any], *keys: str) -> Any:
    candidates = [report, report.get("general", {}) or {}, report.get("identity", {}) or {}]
    wanted = {canonical_key(key) for key in keys}
    for source in candidates:
        normalized = {canonical_key(k): v for k, v in source.items()}
        for key in wanted:
            if key in normalized and normalized[key] not in (None, ""):
                return normalized[key]
    return ""


def first_value(row: dict[str, Any], patterns: Iterable[str]) -> Any:
    canonical_patterns = [canonical_key(pattern) for pattern in patterns]
    for key, value in row.items():
        ckey = canonical_key(key)
        if any(pattern in ckey for pattern in canonical_patterns):
            if value not in (None, ""):
                return value
    return ""


def first_number(row: dict[str, Any], patterns: Iterable[str], default: float = 0.0) -> float:
    value = first_value(row, patterns)
    return to_float(value, default=default)


def row_text(row: dict[str, Any]) -> str:
    return " ".join(str(value) for value in row.values() if value not in (None, "")).lower()


def has_records(records: list[dict[str, Any]]) -> bool:
    for row in records:
        if any(str(value).strip() not in {"", "-", "0", "0,00", "0.00"} for value in row.values()):
            return True
    return False


def sum_numbers(records: list[dict[str, Any]], patterns: Iterable[str]) -> float:
    total = 0.0
    canonical_patterns = [canonical_key(pattern) for pattern in patterns]
    for row in records:
        for key, value in row.items():
            ckey = canonical_key(key)
            if any(pattern in ckey for pattern in canonical_patterns):
                number = normalize_number(value)
                if number is not None:
                    total += float(number)
    return total


def product_name(row: dict[str, Any]) -> str:
    return str(first_value(row, ["produk", "jenis_produk", "uraian_produk", "nama_barang"]) or "").strip()


def hs_code(row: dict[str, Any]) -> str:
    raw = str(first_value(row, ["kode_hs", "hs"]) or "").strip()
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return ""
    if len(digits) >= 8:
        return digits[:8]
    return digits.zfill(8)


def kbli_code(row: dict[str, Any]) -> str:
    raw = str(first_value(row, ["kbli"]) or "").strip()
    match = re.search(r"\d{5}", raw)
    return match.group(0) if match else raw


def is_food_report(report: dict[str, Any]) -> bool:
    text = " ".join(
        [
            str(metadata(report, "kbli", "bidang_usaha")),
            " ".join(row_text(row) for row in section(report, "produksi_penjualan", "kapasitas")),
        ]
    ).lower()
    food_keywords = [
        "makanan",
        "pangan",
        "daging",
        "ayam",
        "sapi",
        "roti",
        "kue",
        "bumbu",
        "saus",
        "penyedap",
    ]
    return any(keyword in text for keyword in food_keywords)


def percent_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None if current == 0 else 100.0
    return ((current - previous) / abs(previous)) * 100.0


def approx_equal(left: float, right: float, tolerance_percent: float) -> bool:
    basis = max(abs(left), abs(right), 1.0)
    return abs(left - right) / basis * 100 <= tolerance_percent
