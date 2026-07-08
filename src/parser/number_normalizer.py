from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any


NUMBER_RE = re.compile(r"[-+]?\d[\d.,]*")
UNIT_RE = re.compile(r"[A-Za-z%/]+(?:\s*[A-Za-z%/]+)*")
CURRENCY_RE = re.compile(r"\b(?:rp\.?|idr|rupiah)\b", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class ParsedNumber:
    value: float | int | None
    unit: str
    original: str


def _coerce_integral(value: float) -> float | int:
    if math.isfinite(value) and abs(value - round(value)) < 1e-9:
        return int(round(value))
    return value


def _parse_numeric_token(token: str) -> float | int | None:
    cleaned = token.strip()
    if not cleaned:
        return None

    sign = -1 if cleaned.startswith("-") else 1
    cleaned = cleaned.lstrip("+-")

    if "," in cleaned:
        # Indonesian format: dots are thousands, comma is decimal.
        normalized = cleaned.replace(".", "").replace(",", ".")
    elif "." in cleaned:
        parts = cleaned.split(".")
        if len(parts) > 2:
            # 21.636.456.226 and similar grouped values.
            normalized = "".join(parts)
        else:
            integer, fraction = parts
            if len(fraction) == 3 and fraction != "000":
                # 1.800 means 1800 in Indonesian reporting.
                normalized = integer + fraction
            elif len(fraction) == 3 and fraction == "000" and len(integer) <= 3:
                # 1.000 and 60.000 are thousands, not decimals.
                normalized = integer + fraction
            elif len(fraction) >= 4 and set(fraction) == {"0"}:
                # System decimal such as 60000.00000.
                normalized = integer
            elif len(fraction) > 3:
                normalized = f"{integer}.{fraction}"
            elif len(integer) > 3 and fraction == "000":
                # 60000.000 is usually a system decimal with zero fraction.
                normalized = integer
            else:
                normalized = f"{integer}.{fraction}"
    else:
        normalized = cleaned

    try:
        return _coerce_integral(float(normalized) * sign)
    except ValueError:
        return None


def normalize_number(value: Any) -> float | int | None:
    """Read Indonesian numeric/currency text into a Python number.

    The function uses reporting-oriented heuristics:
    - comma means decimal separator and dot means thousands separator
    - a single dot followed by exactly 3 digits means thousands
    - a system value such as 60000.00000 is treated as 60000
    """

    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int | float):
        if isinstance(value, float) and math.isnan(value):
            return None
        return _coerce_integral(float(value))

    text = str(value).strip()
    if not text or text in {"-", "–", "—"}:
        return None

    negative_parentheses = text.startswith("(") and text.endswith(")")
    text = CURRENCY_RE.sub("", text)
    text = text.replace("\xa0", " ").replace("−", "-")
    match = NUMBER_RE.search(text)
    if not match:
        return None
    parsed = _parse_numeric_token(match.group(0))
    if parsed is None:
        return None
    if negative_parentheses:
        parsed = -parsed
    return parsed


def parse_number_with_unit(value: Any) -> ParsedNumber:
    original = "" if value is None else str(value).strip()
    if value is None:
        return ParsedNumber(None, "", original)

    text = original.replace("\xa0", " ")
    text_without_currency = CURRENCY_RE.sub("", text)
    match = NUMBER_RE.search(text_without_currency)
    if not match:
        return ParsedNumber(None, "", original)

    number = normalize_number(text_without_currency)
    after = text_without_currency[match.end() :].strip(" :;-")
    unit_match = UNIT_RE.search(after)
    unit = unit_match.group(0).strip() if unit_match else ""
    return ParsedNumber(number, unit, original)


def to_float(value: Any, default: float = 0.0) -> float:
    parsed = normalize_number(value)
    if parsed is None:
        return default
    return float(parsed)


def format_rupiah(value: float | int | None) -> str:
    if value is None:
        return "-"
    return f"Rp{int(round(float(value))):,}".replace(",", ".")

