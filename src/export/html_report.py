from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from src.insight.narrative import findings_table, generate_full_narrative, section_recommendations_table
from src.storage.models import ValidationResult


def export_html_report(report: dict[str, Any], result: ValidationResult, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = findings_table(result.findings)
    table_rows = "\n".join(
        "<tr>"
        + "".join(f"<td>{html.escape(str(row.get(col, '')))}</td>" for col in ["Kategori", "Rule", "Severity", "Status", "Temuan", "Nilai", "Rekomendasi"])
        + "</tr>"
        for row in rows
    )
    narrative = html.escape(generate_full_narrative(report, result)).replace("\n", "<br>")
    section_rows = "\n".join(
        "<tr>"
        + "".join(
            f"<td>{html.escape(str(row.get(col, '')))}</td>"
            for col in ["Bagian", "Rekomendasi", "Risk Score Bagian", "Critical", "High", "Medium", "Low", "Temuan Utama"]
        )
        + "</tr>"
        for row in section_recommendations_table(result.findings)
    )
    document = f"""<!doctype html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <title>Laporan Validasi - {html.escape(str(report.get("company_name", "")))}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f2937; }}
    h1 {{ font-size: 24px; }}
    .score {{ font-size: 20px; font-weight: 700; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px; vertical-align: top; font-size: 12px; }}
    th {{ background: #f3f4f6; text-align: left; }}
  </style>
</head>
<body>
  <h1>{html.escape(str(report.get("company_name", "Perusahaan")))}</h1>
  <p>Periode: {html.escape(str(report.get("period", "-")))}</p>
  <p class="score">Risk score: {result.risk_score}/100</p>
  <p>Rekomendasi: {html.escape(result.recommendation)}</p>
  <div>{narrative}</div>
  <h2>Rekomendasi Per Bagian</h2>
  <table>
    <thead>
      <tr><th>Bagian</th><th>Rekomendasi</th><th>Risk Score Bagian</th><th>Critical</th><th>High</th><th>Medium</th><th>Low</th><th>Temuan Utama</th></tr>
    </thead>
    <tbody>{section_rows}</tbody>
  </table>
  <h2>Tabel Validasi</h2>
  <table>
    <thead>
      <tr><th>Kategori</th><th>Rule</th><th>Severity</th><th>Status</th><th>Temuan</th><th>Nilai</th><th>Rekomendasi</th></tr>
    </thead>
    <tbody>{table_rows}</tbody>
  </table>
</body>
</html>"""
    path.write_text(document, encoding="utf-8")
    return path
