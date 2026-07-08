from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.insight.narrative import findings_table, section_recommendations_table
from src.storage.models import ValidationFinding, ValidationResult


def _safe_sheet_name(name: str) -> str:
    invalid = "[]:*?/\\"
    cleaned = "".join("_" if char in invalid else char for char in name)
    return cleaned[:31] or "Sheet"


def export_report_excel(
    report: dict[str, Any],
    findings: list[ValidationFinding],
    result: ValidationResult,
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        summary = pd.DataFrame(
            [
                {
                    "company_name": report.get("company_name", ""),
                    "period": report.get("period", ""),
                    "status": report.get("status", ""),
                    "risk_score": result.risk_score,
                    "recommendation": result.recommendation,
                    **result.severity_counts,
                }
            ]
        )
        summary.to_excel(writer, index=False, sheet_name="Ringkasan")
        pd.DataFrame(section_recommendations_table(findings)).to_excel(writer, index=False, sheet_name="Rekomendasi Bagian")
        pd.DataFrame(findings_table(findings)).to_excel(writer, index=False, sheet_name="Validasi")
        for section_name, rows in (report.get("sections") or {}).items():
            if isinstance(rows, list) and rows:
                pd.DataFrame(rows).to_excel(writer, index=False, sheet_name=_safe_sheet_name(section_name))
        raw = pd.DataFrame(
            [
                {"field": "raw_html_path", "value": report.get("raw_html_path", "")},
                {"field": "raw_csv_paths", "value": "\n".join(report.get("raw_csv_paths", []) or [])},
            ]
        )
        raw.to_excel(writer, index=False, sheet_name="Raw Data")
    return path
